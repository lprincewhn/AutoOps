import boto3
import gzip
import json
import datetime
import requests
from requests_aws4auth import AWS4Auth

region = 'us-east-1' # e.g. us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'https://es.svhw.tech' 

headers = { "Content-Type": "application/json" }

s3 = boto3.client('s3')

def lambda_handler(event, context):
    for record in event['Records']:

        # Get the bucket name and key for the new file
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        print(f'Processing s3://{bucket}/{key}')
        # Get, read, and split the file into lines
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = obj['Body'].read()
        print(f'Length of gz file: {len(data)}.')
        logs = gzip.decompress(data).decode().split('\n')
        cols = logs[1].split()
        cnt = 0
        for line in logs[2:]:
            values = line.split()
            item = dict(zip(cols[1:], values))
            if item:
                item["timestamp"] = datetime.datetime.strptime(f'{item["date"]} {item["time"]}', '%Y-%m-%d %H:%M:%S').timestamp()
                index = f'cloudfront-standard-log-{item["date"]}'
                url = host + '/' + index + '/_doc'
                print(f'URL: {url}')
                print(f'DATA: {item}')
                r = requests.post(url, auth=awsauth, json=item, headers=headers)
                print(r)
                print(r.text)
                cnt += 1
        print(f'Done. {cnt} logs sent.')
        return cnt

