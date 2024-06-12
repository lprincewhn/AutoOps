import os
import re
import boto3
import json
import math
import datetime
import logging
import requests

logging.basicConfig()
logger = logging.getLogger("DialTest")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)


# 环境变量参数
namespace = os.getenv('CLOUDWATCH_NAMESPACE', 'DialTest')
dims = '[' + os.getenv('CLOUDWATCH_DIMENSIONS', '["Target"],["Target", "City"]') + ']' 
peroid = int(os.getenv('CLOUDWATCH_PERIOD_SECS', '60'))*1000
use_emf = os.getenv('USE_EMF', '1')
cf_domainname = os.getenv('CLOUDFRONT_DOMAINNAME')
pop_list = os.getenv('CLOUDFRONT_POPLIST')
dial_domainname = os.getenv('DIAL_DOMAINNAME')
dial_uri = os.getenv('DIAL_URI')

def parseTimingHeader(results, metrics):
    for result in results:
        logger.debug(f'Item: {result}')
        record = {}
        record["timestamp"] = datetime.datetime.now().timestamp()*1000
        record['cdn-upstream-succ'] = (1 if result[1]==200 else 0)
        timing = result[2]
        match = re.match('.*cdn-upstream-dns;dur=(\d+)', timing)
        record['cdn-upstream-dns'] = match.group(1) if match else 0
        match = re.match('.*cdn-upstream-connect;dur=(\d+)', timing)
        record['cdn-upstream-connect'] = match.group(1) if match else 0
        match = re.match('.*cdn-upstream-fbl;dur=(\d+)', timing)
        record['cdn-upstream-fbl'] = match.group(1) if match else 0
        match = re.match('.*cdn-pop;desc=\"(.+?)\"', timing)
        record['cdn-city'] = match.group(1)[:3] if match else result[0][:3]

        # 计算聚合指标，准备通过emf发送到CloudWatch
        metric_key = (
            int(record["timestamp"]/peroid)*peroid,
            record['cdn-city'], 
            dial_domainname
        )
        
        metrics['cdn-upstream-succ-sum'][metric_key] = metrics['cdn-upstream-succ-sum'].get(metric_key, 0) + record['cdn-upstream-succ']
        metrics['cdn-upstream-succ-cnt'][metric_key] = metrics['cdn-upstream-succ-cnt'].get(metric_key, 0) + 1
        if int(record['cdn-upstream-succ'])>metrics['cdn-upstream-succ-max'].get(metric_key, 0):
            metrics['cdn-upstream-succ-max'][metric_key] = int(record['cdn-upstream-succ'])
        if int(record['cdn-upstream-succ'])<metrics['cdn-upstream-succ-min'].get(metric_key, 0):
            metrics['cdn-upstream-dns-min'][metric_key] = int(record['cdn-upstream-succ'])

        metrics['cdn-upstream-dns-sum'][metric_key] = metrics['cdn-upstream-dns-sum'].get(metric_key, 0) + int(record['cdn-upstream-dns'])
        metrics['cdn-upstream-dns-cnt'][metric_key] = metrics['cdn-upstream-dns-cnt'].get(metric_key, 0) + 1
        if int(record['cdn-upstream-dns'])>metrics['cdn-upstream-dns-max'].get(metric_key, 0):
            metrics['cdn-upstream-dns-max'][metric_key] = int(record['cdn-upstream-dns'])
        if int(record['cdn-upstream-dns'])<metrics['cdn-upstream-dns-min'].get(metric_key, 0):
            metrics['cdn-upstream-dns-min'][metric_key] = int(record['cdn-upstream-dns'])
        
        metrics['cdn-upstream-connect-sum'][metric_key] = metrics['cdn-upstream-connect-sum'].get(metric_key, 0) + int(record['cdn-upstream-connect'])
        metrics['cdn-upstream-connect-cnt'][metric_key] = metrics['cdn-upstream-connect-cnt'].get(metric_key, 0) + 1
        if int(record['cdn-upstream-connect'])>metrics['cdn-upstream-connect-max'].get(metric_key, 0):
            metrics['cdn-upstream-connect-max'][metric_key] = int(record['cdn-upstream-connect'])
        if int(record['cdn-upstream-connect'])<metrics['cdn-upstream-connect-min'].get(metric_key, 0):
            metrics['cdn-upstream-connect-min'][metric_key] = int(record['cdn-upstream-connect'])

        metrics['cdn-upstream-fbl-sum'][metric_key] = metrics['cdn-upstream-fbl-sum'].get(metric_key, 0) + int(record['cdn-upstream-fbl'])
        metrics['cdn-upstream-fbl-cnt'][metric_key] = metrics['cdn-upstream-fbl-cnt'].get(metric_key, 0) + 1
        if int(record['cdn-upstream-fbl'])>metrics['cdn-upstream-fbl-max'].get(metric_key, 0):
            metrics['cdn-upstream-fbl-max'][metric_key] = int(record['cdn-upstream-fbl'])
        if int(record['cdn-upstream-fbl'])<metrics['cdn-upstream-fbl-min'].get(metric_key, 999999999):
            metrics['cdn-upstream-fbl-min'][metric_key] = int(record['cdn-upstream-fbl'])

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}...')
    results = []
    for popid in pop_list.split(','):
        url = f'http://{cf_domainname.split(".")[0]}.{popid}.cloudfront.net{dial_uri}'
        for i in range(2):
            try:
                logger.debug(url)
                r = requests.head(url, headers={'Host': cf_domainname}, timeout=10, stream=True)
                # print(r.raw._connection.sock.getpeername()[0])
                t = r.headers.get('Server-Timing')
                results.append((popid, r.status_code, t))
            except Exception as e:
                logger.warning(e)
                results.append((popid, 0, ''))

    metrics = {
        'cdn-upstream-succ-cnt':{},'cdn-upstream-succ-sum':{},'cdn-upstream-succ-max':{},'cdn-upstream-succ-min':{},
        'cdn-upstream-dns-cnt':{}, 'cdn-upstream-dns-sum':{}, 'cdn-upstream-dns-max':{}, 'cdn-upstream-dns-min':{}, 
        'cdn-upstream-connect-cnt':{}, 'cdn-upstream-connect-sum':{}, 'cdn-upstream-connect-max':{}, 'cdn-upstream-connect-min':{}, 
        'cdn-upstream-fbl-cnt':{}, 'cdn-upstream-fbl-sum':{}, 'cdn-upstream-fbl-max':{}, 'cdn-upstream-fbl-min':{}
    }
    parseTimingHeader(results, metrics)

    # 将聚合后指标发送到CloudWatch
    metricList = []
    log_size = 0
    for k,v in metrics['cdn-upstream-fbl-sum'].items():
        emfdata = {
            'City': k[1],
            'Target': k[2],
            '_aws': {
                'Timestamp': k[0],
                'CloudWatchMetrics': [
                    {
                        'Dimensions': json.loads(dims),
                        'Metrics': [
                            {
                                'Name': 'cdn-upstream-succ'
                            },
                            {
                                'Name': 'cdn-upstream-req'
                            },
                            {
                                'Name': 'cdn-upstream-dns'
                            },
                            {
                                'Name': 'cdn-upstream-connect'
                            },
                            {
                                'Name': 'cdn-upstream-fbl'
                            },
                        ],
                        'Namespace': namespace
                    }
                ]
            },
            'cdn-upstream-succ': metrics['cdn-upstream-succ-sum'].get(k, 0),
            'cdn-upstream-req': metrics['cdn-upstream-succ-cnt'].get(k, 0),
            'cdn-upstream-dns': metrics['cdn-upstream-dns-sum'].get(k, 0)/metrics['cdn-upstream-dns-cnt'].get(k, -1),
            'cdn-upstream-connect': metrics['cdn-upstream-connect-sum'].get(k, 0)/metrics['cdn-upstream-connect-cnt'].get(k, -1),
            'cdn-upstream-fbl': metrics['cdn-upstream-fbl-sum'].get(k, 0)/metrics['cdn-upstream-fbl-cnt'].get(k, -1)
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
                    'MetricName': 'cdn-upstream-succ',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'StatisticValues': {
                        'SampleCount': int(metrics['cdn-upstream-succ-cnt'].get(k, 0)),
                        'Sum': int(metrics['cdn-upstream-succ-sum'].get(k, 0)),
                        'Minimum': int(metrics['cdn-upstream-succ-min'].get(k, 0)),
                        'Maximum': int(metrics['cdn-upstream-succ-max'].get(k, 0))
                    },
                    'Unit': 'Count',
                    'StorageResolution': 60
                },
                {
                    'MetricName': 'cdn-upstream-req',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'StatisticValues': {
                        'SampleCount': int(metrics['cdn-upstream-succ-cnt'].get(k, 0)),
                        'Sum': int(metrics['cdn-upstream-succ-cnt'].get(k, 0)),
                        'Minimum': int(metrics['cdn-upstream-succ-cnt'].get(k, 0)),
                        'Maximum': int(metrics['cdn-upstream-succ-cnt'].get(k, 0))
                    },
                    'Unit': 'Count',
                    'StorageResolution': 60
                },                
                {
                    'MetricName': 'cdn-upstream-dns',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'StatisticValues': {
                        'SampleCount': metrics['cdn-upstream-dns-cnt'].get(k, 0),
                        'Sum': int(metrics['cdn-upstream-dns-sum'].get(k, 0)),
                        'Minimum': int(metrics['cdn-upstream-dns-min'].get(k, 0)),
                        'Maximum': int(metrics['cdn-upstream-dns-max'].get(k, 0))
                    },
                    'Unit': 'Milliseconds',
                    'StorageResolution': 60
                },
                {
                    'MetricName': 'cdn-upstream-connect',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'StatisticValues': {
                        'SampleCount': metrics['cdn-upstream-connect-cnt'].get(k, 0),
                        'Sum': int(metrics['cdn-upstream-connect-sum'].get(k, 0)),
                        'Minimum': int(metrics['cdn-upstream-connect-min'].get(k, 0)),
                        'Maximum': int(metrics['cdn-upstream-connect-max'].get(k, 0))
                    },
                    'Unit': 'Milliseconds',
                    'StorageResolution': 60
                },
                {
                    'MetricName': 'cdn-upstream-fbl',
                    'Dimensions': dimensions,
                    'Timestamp': datetime.datetime.fromtimestamp(k[0]/1000),
                    'StatisticValues': {
                        'SampleCount': metrics['cdn-upstream-fbl-cnt'].get(k, 0),
                        'Sum': int(metrics['cdn-upstream-fbl-sum'].get(k, 0)),
                        'Minimum': int(metrics['cdn-upstream-fbl-min'].get(k, 0)),
                        'Maximum': int(metrics['cdn-upstream-fbl-max'].get(k, 0))
                    },
                    'Unit': 'Milliseconds',
                    'StorageResolution': 60
                },
            ]
    
    logger.info(f'payload of put_metric_data(): {str(metricList)}')
    logger.info(f'Size of put_metric_data(): {len(str(metricList))}')
    logger.info(f'Size of EMF Log: {log_size}')

    batch = math.ceil(len(str(metricList))/40960)
    batch_items = math.ceil(len(metricList)/batch)
    logger.info(f'API Batchs: {len(str(metricList))}:{batch}:{batch_items}')

    if not use_emf:
        cloudwatch = boto3.client('cloudwatch')
        for i in range(batch): 
            start = i * batch_items
            end = (i+1) * batch_items
            logger.info(f'Batch {i}: {start}:{end}')
            try:
                response = cloudwatch.put_metric_data(
                    Namespace=namespace,
                    MetricData=metricList[start:end]
                )
                logger.info(response)
            except Exception as e:
                logger.warning(e)

if __name__ == '__main__':
    lambda_handler(None, None)
