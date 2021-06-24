import os
import boto3
import gzip
import json
import datetime
import requests
import logging
from requests_aws4auth import AWS4Auth

logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def deliverToES(data):
    es_region = os.getenv("ESRegion")
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, es_region, 'es', session_token=credentials.token)
    host = os.getenv("ESEndpoint")
    headers = { "Content-Type": "application/json" }
    url = host + '/_bulk'
    logger.info(f'URL: {url}')
    logger.debug(f'DATA: {data}')
    r = requests.post(url, auth=awsauth, data=data, headers=headers)
    logger.info(f'{r.text[:100]}...')

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
        logs = gzip.decompress(data).decode().split('\n')
        cols = logs[1].split()
        cnt = 0
        batch = int(os.getenv("BatchSize", 400))
        for i in range(2,len(logs),batch):
            request_data = ""
            for line in logs[i:i+batch]:
                if line.startswith('#') or len(line)<10:
                    continue
                values = line.split()
                item = dict(zip(cols[1:], values))
                if item:
                    item["timestamp"] = datetime.datetime.strptime(f'{item["date"]} {item["time"]}', '%Y-%m-%d %H:%M:%S').timestamp()*1000
                    index = f'cloudfront-access-log-{item["date"]}'
                    request_data += json.dumps({"index":{"_index" :index}}) + "\n"
                    request_data += json.dumps(item) + "\n"
                    cnt += 1
            deliverToES(request_data)
        logger.info(f'Done. {cnt} logs sent.')
        return cnt

