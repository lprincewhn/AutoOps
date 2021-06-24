import os
import re
import boto3
import gzip
import json
import datetime
import requests
import logging
import requests_aws4auth
from urllib.parse import unquote

logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def parseUserActivityLog(key, data):
    keyary = key.split('/')[-1].split('_')
    items = re.split("\n'", data)
    records = []
    for i in items:
        logger.debug(f"Item: {i}")
        reg = re.compile("^(?P<recordtime>[^ ]*) UTC \[ db=(?P<db>[^ ]*) user=(?P<user>[^ ]*) pid=(?P<pid>[^ ]*) userid=(?P<userid>[^ ]*) xid=(?P<xid>[^ ]*) \]' LOG: (?P<query>.*)", re.DOTALL)
        regMatch = reg.match(i[1:]) if i.startswith("'") else reg.match(i)
        if regMatch:
            record = regMatch.groupdict()
            record['timestamp'] = datetime.datetime.strptime(record['recordtime'], '%Y-%m-%dT%H:%M:%SZ').timestamp()*1000
            record['account_id'] = keyary[0]
            record['region'] = keyary[2]
            record['cluster_id'] = keyary[3]
            records.append(record)
    return records 

def parseUserLog(key, data):
    keyary = key.split('/')[-1].split('_')
    items = re.split("\n", data)
    records = []
    for i in items:
        logger.debug(f"Item: {i}")
        fields = i.split('|')
        if len(fields)>=10:
            record = {
                "userid": fields[0],
                "username": fields[1],
                "oldusername": fields[2],
                "action": fields[3],
                "usecreatedb": fields[4],  
                "usesuper": fields[5],
                "usecatupd": fields[6],
                "valuntil": fields[7],
                "pid": fields[8],
                "xid": fields[9],  
                "recordtime": fields[10]
              }
            record["timestamp"] = datetime.datetime.strptime(fields[10], '%a, %d %b %Y %H:%M:%S:%f').timestamp()*1000
            record['account_id'] = keyary[0]
            record['region'] = keyary[2]
            record['cluster_id'] = keyary[3]
            records.append(record)
    return records 

def parseConnectionLog(key, data):
    keyary = key.split('/')[-1].split('_')
    items = re.split("\n", data)
    records = []
    for i in items:
        logger.debug(f"Item: {i}")
        fields = i.split('|')
        if len(fields)>=19:
            record = {
                "event": fields[0],
                "recordtime": fields[1],
                "remotehost": fields[2],
                "remoteport": fields[3],
                "pid": fields[4],  
                "dbname": fields[5],
                "username": fields[6],
                "authmethod": fields[7],
                "duration": fields[8],
                "sslversion": fields[9],  
                "sslcipher": fields[10],
                "mtu": fields[11],
                "sslcompression": fields[12],
                "sslexpansion": fields[13],
                "iamauthguid": fields[14],                    
                "application_name": fields[15],
                "driver_version": fields[16],
                "os_version": fields[17],
                "plugin_name": fields[18]
              }
            record["timestamp"] = datetime.datetime.strptime(fields[1], '%a, %d %b %Y %H:%M:%S:%f').timestamp()*1000
            record['account_id'] = keyary[0]
            record['region'] = keyary[2]
            record['cluster_id'] = keyary[3]
            records.append(record)
    return records 

def deliverToES(data):
    es_region = os.getenv("ESRegion")
    credentials = boto3.Session().get_credentials()
    awsauth = requests_aws4auth.AWS4Auth(credentials.access_key, credentials.secret_key, es_region, 'es', session_token=credentials.token)
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
        obj = s3.get_object(Bucket=bucket, Key=unquote(key))
        data = obj['Body'].read()
        logger.info(f'Length of gz file: {len(data)}.')
        logs = gzip.decompress(data).decode()
        records = []
        if 'useractivitylog' in key:
            records = parseUserActivityLog(key, logs)
        elif 'connectionlog' in key:
            records = parseConnectionLog(key, logs)
        elif 'userlog' in key:
            records = parseUserLog(key, logs)
        cnt = 0
        batch = int(os.getenv("BatchSize", 1000))
        for i in range(0,len(records),batch):
            request_data = ""
            for record in records[i:i+batch]:
                if record:
                    index = f'redshift-audit-log-{datetime.datetime.strftime(datetime.datetime.utcfromtimestamp(record["timestamp"]/1000), "%Y-%m-%d")}'
                    request_data += json.dumps({"index":{"_index" :index}}) + "\n"
                    request_data += json.dumps(record) + "\n"
                    cnt += 1
            deliverToES(request_data)
        logger.info(f'Done. {cnt} logs sent.')
        return cnt

