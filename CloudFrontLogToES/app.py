import os
import re
import boto3
import gzip
import json
import datetime
import logging

logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

s3 = boto3.client('s3')
firehose = boto3.client('firehose')

def parseCloudFrontLog(key, cols, data):
    keyary = key.split('/')[-1].split('_')
    records = []
    for line in data:
        logger.debug(f'Item: {line}')
        if line.startswith('#') or len(line)<10:
            continue
        values = line.split()
        record = dict(zip(cols[1:], values))
        if record:
            record["timestamp"] = datetime.datetime.strptime(f'{record["date"]} {record["time"]}', '%Y-%m-%d %H:%M:%S').timestamp()*1000
            records.append({'Data': json.dumps(record).encode('utf-8')})
    if records:
        response = firehose.put_record_batch(
            DeliveryStreamName=os.getenv("FIREHOSE_STREAM_NAME"),
            Records=records
        )
        logger.info(f'Response: {json.dumps(response)[:100]}...')
    logger.info(f'{len(records)} of {len(data)} lines delivered.')
    return records

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}...')
    s3 = boto3.client('s3')
    for record in event['Records']:
        # Get the bucket name and key for the new file
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        logger.info(f'Processing s3://{bucket}/{key}')
        # Get, read, and split the file into lines
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = obj['Body'].read()
        logger.info(f'Length of gz file: {len(data)}.')
        logs = gzip.decompress(data).decode()
        items = re.split("\n", logs)
        cols = items[1].split()
        logger.info(f'Cols: {cols}')
        # Kinesis Firehose每次最多接受500条记录, 因此分批下载日志，每批500行，当返回行数>=500时，继续下载，小于500时表示下载完毕。
        for start in range(2,len(items),500):
            parseCloudFrontLog(key, cols, items[start:start+500])

