import os
import re
import os
import boto3
import gzip
import json
import datetime
import logging
import geoip2.database

logging.basicConfig()
logger = logging.getLogger("VisualizeCloudFrontLog")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

s3 = boto3.client('s3')
firehose = boto3.client('firehose')

def parseCloudFrontLog(key, cols, data, records):
    keyary = key.split('/')[-1].split('_')
    countryreader = geoip2.database.Reader('GeoLite2-Country_20220510/GeoLite2-Country.mmdb')
    cityreader = geoip2.database.Reader('GeoLite2-City_20220510/GeoLite2-City.mmdb')
    asnreader = geoip2.database.Reader('GeoLite2-ASN_20220510/GeoLite2-ASN.mmdb')

    for line in data:
        logger.debug(f'Item: {line}')
        if line.startswith('#') or len(line)<10:
            continue
        values = line.split()
        record = dict(zip(cols[1:], values))
        if record:
            # 日志格式转换，准备发送到Firehose和ES
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
                
            records.append({'Data': json.dumps(record).encode('utf-8')})                


def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}...')
    s3 = boto3.client('s3')
    # Get the bucket name and key for the new file
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']
    logger.info(f'Processing s3://{bucket}/{key}')
    logger.info(f'Processing s3://{bucket}/{key}')
    # Get, read, and split the file into lines
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read()
    logger.info(f'Length of gz file: {len(data)}.')
    logs = gzip.decompress(data).decode()
    items = re.split("\n", logs)
    cols = items[1].split()
    logger.info(f'Cols: {cols}')
    # Kinesis Firehose每次最多接受500条记录, 因此分批处理日志，每批500行。
    for start in range(2,len(items),500):
        logger.info(f'Processing {start}th line of {len(items)}.')
        records = []
        parseCloudFrontLog(key, cols, items[start:start+500], records)
        if records:
            response = firehose.put_record_batch(
                DeliveryStreamName=os.getenv("FIREHOSE_STREAM_NAME"),
                Records=records
            )
            logger.info(f'Response: {json.dumps(response)[:100]}...')
        logger.info(f'{len(records)} records delivered.')


