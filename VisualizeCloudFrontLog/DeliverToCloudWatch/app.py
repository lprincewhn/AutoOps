import os
import re
import boto3
import gzip
import json
import math
import datetime
import logging
import geoip2.database

logging.basicConfig()
logger = logging.getLogger("VisualizeCloudFrontLog")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)


# 环境变量参数
namespace = os.getenv('CLOUDWATCH_NAMESPACE', 'CloudFrontLogs')
dims = '[' + os.getenv('CLOUDWATCH_DIMENSIONS', '[],["Host"],["Host", "Country"],["Host", "Country","ResponseCode"]') + ']' 
peroid = int(os.getenv('CLOUDWATCH_PERIOD_SECS', '60'))*1000
use_emf = os.getenv('USE_EMF', '1')
use_metric_api = os.getenv('USE_METRIC_API', '1')

countryreader = geoip2.database.Reader('GeoLite2-Country_20220510/GeoLite2-Country.mmdb')
cityreader = geoip2.database.Reader('GeoLite2-City_20220510/GeoLite2-City.mmdb')
asnreader = geoip2.database.Reader('GeoLite2-ASN_20220510/GeoLite2-ASN.mmdb')

def parseCloudFrontLog(key, cols, data, metrics):
    keyary = key.split('/')[-1].split('_')
    for line in data:
        logger.debug(f'Item: {line}')
        if line.startswith('#') or len(line)<10:
            # 过滤掉表头和太短的数据行
            continue
        values = line.split()
        record = dict(zip(cols[1:], values))
        if record:
            # 日志格式转换
            record["timestamp"] = datetime.datetime.strptime(f'{record["date"]} {record["time"]}', '%Y-%m-%d %H:%M:%S').timestamp()*1000
            try:
                response = asnreader.asn(record['c-ip'])
                record['autonomous_system_number'] = response.autonomous_system_number
                record['autonomous_system_organization'] = response.autonomous_system_organization
            except Exception as e:
                logger.warn(e)
                record['autonomous_system_number'] = 'unknown'
            try:
                response = countryreader.country(record['c-ip'])
                record['continent'] = response.continent.names.get('en', 'unknown')
                record['country'] = response.country.names.get('en', 'unknown')
            except Exception as e:
                logger.warn(e)
                record['country'] = 'unknown'
            try:
                response = cityreader.city(record['c-ip'])
                record['city'] = response.city.names.get('en', 'unknown')
            except Exception as e:
                logger.warn(e)
                record['city'] = 'unknown'            

            # 计算聚合指标，准备通过emf发送到CloudWatch
            metric_key = (
                int(record["timestamp"]/peroid)*peroid,
                record['x-host-header'], 
                record['country'], 
                record['autonomous_system_number'], 
                record['sc-status'], 
                record['x-edge-response-result-type']
            )
            metrics['Requests'][metric_key] = metrics['Requests'].get(metric_key, 0) + 1
            metrics['BytesDownloaded'][metric_key] = metrics['BytesDownloaded'].get(metric_key, 0) + int(record['sc-bytes'])
            metrics['BytesUploaded'][metric_key] = metrics['BytesUploaded'].get(metric_key, 0) + int(record['cs-bytes'])
            speeddownload = int(record['sc-bytes'])/float(record['time-taken'])
            metrics['SpeedDownloadSampleCount'][metric_key] = metrics['SpeedDownloadSampleCount'].get(metric_key, 0) + 1
            metrics['SpeedDownloadSum'][metric_key] = metrics['SpeedDownloadSum'].get(metric_key, 0) + speeddownload
            if speeddownload>metrics['SpeedDownloadMax'].get(metric_key, 0):
                metrics['SpeedDownloadMax'][metric_key] = speeddownload
            if speeddownload<metrics['SpeedDownloadMin'].get(metric_key, 1000000000000000):
                metrics['SpeedDownloadMin'][metric_key] = speeddownload

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}...')
    s3 = boto3.client('s3')
    # Get the bucket name and key for the new file
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']
    logger.info(f'Processing s3://{bucket}/{key}')
    # Get, read, and split the file into lines
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read()
    logger.info(f'Length of gz file: {len(data)}.')
    logs = gzip.decompress(data).decode()
    items = re.split("\n", logs)
    cols = items[1].split()
    logger.info(f'Cols: {cols}')

    metrics = {
        'Requests':{}, 'BytesDownloaded': {}, 'BytesUploaded': {}, 
        'SpeedDownloadSampleCount': {}, 'SpeedDownloadSum': {},
        'SpeedDownloadMax': {}, 'SpeedDownloadMin': {}
        }
    parseCloudFrontLog(key, cols, items, metrics)

    # 将聚合后指标发送到CloudWatch
    metricList = []
    log_size = 0
    for k,v in metrics['Requests'].items():
        emfdata = {
            'SourceFile': f's3://{bucket}/{key}',
            'Host': k[1],
            'Country': k[2],
            'ASN': k[3],
            'ResponseCode': k[4],
            'ResultType': k[5],
            '_aws': {
                'Timestamp': k[0],
                'CloudWatchMetrics': [
                    {
                        'Dimensions': json.loads(dims),
                        'Metrics': [
                            {
                                'Name': 'Requests'
                            },
                            {
                                'Name': 'BytesDownloaded',
                                'Unit': 'Bytes'
                            },
                            {
                                'Name': 'BytesUploaded',
                                'Unit': 'Bytes'
                            },
                        ],
                        'Namespace': namespace
                    }
                ]
            },
            'Requests': v,
            'BytesDownloaded': metrics['BytesDownloaded'].get(k, 0),
            'BytesUploaded': metrics['BytesUploaded'].get(k, 0)
        }
        if use_emf:
            print(json.dumps(emfdata))
        
        log_size+=len(json.dumps(emfdata))
        for dim in json.loads(dims):
            dimensions = []
            for name in dim:
                value = emfdata.get(name)
                dimensions.append({'Name': name, 'Value': value})
            metricList += [
                {
                    'MetricName': 'Requests',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'Value': v,
                    'Unit': 'Count',
                    'StorageResolution': 60
                },
                {
                    'MetricName': 'BytesDownloaded',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'Value': metrics['BytesDownloaded'].get(k, 0),
                    'Unit': 'Bytes',
                    'StorageResolution': 60
                },
                {
                    'MetricName': 'BytesUploaded',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'Value': metrics['BytesUploaded'].get(k, 0),
                    'Unit': 'Bytes',
                    'StorageResolution': 60
                },
                {
                    'MetricName': 'SpeedDownload',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'StatisticValues': {
                        'SampleCount': metrics['SpeedDownloadSampleCount'].get(k, 0),
                        'Sum': int(metrics['SpeedDownloadSum'].get(k, 0)),
                        'Minimum': int(metrics['SpeedDownloadMin'].get(k, 0)),
                        'Maximum': int(metrics['SpeedDownloadMax'].get(k, 0))
                    },
                    'Unit': 'Bytes/Second',
                    'StorageResolution': 60
                },
            ]
    
    logger.info(f'payload of put_metric_data(): {str(metricList)}')
    logger.info(f'Size of put_metric_data() in s3://{bucket}/{key}: {len(str(metricList))}')
    logger.info(f'Size of EMF Log in s3://{bucket}/{key}: {log_size}')

    if use_metric_api:
        batch = math.ceil(len(str(metricList))/40960)
        batch_items = math.ceil(len(metricList)/batch)
        logger.info(f'{len(str(metricList))}:{batch}:{batch_items}')
        cloudwatch = boto3.client('cloudwatch')
        for i in range(batch): 
            start = i * batch_items
            end = (i+1) * batch_items
            logger.info(f'{start}:{end}')
            try:
                response = cloudwatch.put_metric_data(
                    Namespace='test',
                    MetricData=metricList[start:end]
                )
                logger.info(response)
            except Exception as e:
                logger.warn(e)


