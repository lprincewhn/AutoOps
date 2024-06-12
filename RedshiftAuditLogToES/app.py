import os
import re
import boto3
import gzip
import json
import datetime
import logging
from urllib.parse import unquote

logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

s3 = boto3.client('s3')
firehose = boto3.client('firehose')

def parseUserActivityLog(key, data):
    keyary = key.split('/')[-1].split('_')
    records = []
    for i in data:
        logger.debug(f"Item: {i}")
        reg = re.compile("^(?P<recordtime>[^ ]*) UTC \[ db=(?P<db>[^ ]*) user=(?P<user>[^ ]*) pid=(?P<pid>[^ ]*) userid=(?P<userid>[^ ]*) xid=(?P<xid>[^ ]*) \]' LOG: (?P<query>.*)", re.DOTALL)
        regMatch = reg.match(i[1:]) if i.startswith("'") else reg.match(i)
        if regMatch:
            record = regMatch.groupdict()
            record['timestamp'] = datetime.datetime.strptime(record['recordtime'], '%Y-%m-%dT%H:%M:%SZ').timestamp()*1000
            record['account_id'] = keyary[0].strip()
            record['region'] = keyary[2].strip()
            record['cluster_id'] = keyary[3].strip()
            logger.debug(f'Record: {record}')
            records.append({'Data': json.dumps(record).encode('utf-8')})
    if records:
        response = firehose.put_record_batch(
            DeliveryStreamName=os.getenv("FIREHOSE_STREAM_NAME"),
            Records=records
        )
        logger.info(f'Response: {json.dumps(response)[:100]}...')
    logger.info(f'{len(records)} of {len(data)} lines delivered.')

def parseUserLog(key, data):
    keyary = key.split('/')[-1].split('_')
    records = []
    for i in data:
        logger.debug(f"Item: {i}")
        fields = i.split('|')
        if len(fields)>=10:
            record = {
                "userid": fields[0].strip(),
                "username": fields[1].strip(),
                "oldusername": fields[2].strip(),
                "action": fields[3],
                "usecreatedb": fields[4].strip(),  
                "usesuper": fields[5].strip(),
                "usecatupd": fields[6].strip(),
                "valuntil": fields[7],
                "pid": fields[8].strip(),
                "xid": fields[9].strip(),  
                "recordtime": fields[10]
            }
            record["timestamp"] = datetime.datetime.strptime(fields[10], '%a, %d %b %Y %H:%M:%S:%f').timestamp()*1000
            record['account_id'] = keyary[0]
            record['region'] = keyary[2]
            record['cluster_id'] = keyary[3]
            logger.debug(f'Record: {record}')
            records.append({'Data': json.dumps(record).encode('utf-8')})
            
    if records:
        response = firehose.put_record_batch(
            DeliveryStreamName=os.getenv("FIREHOSE_STREAM_NAME"),
            Records=records
        )
        logger.info(f'Response: {json.dumps(response)[:100]}...')
    logger.info(f'{len(records)} of {len(data)} lines delivered.')

def parseConnectionLog(key, data):
    keyary = key.split('/')[-1].split('_')
    records = []
    for i in data:
        logger.info(f"Item: {i}")
        fields = i.split('|')
        if len(fields)>=19:
            record = {
                "event": fields[0].strip(),
                "recordtime": fields[1].strip(),
                "remotehost": fields[2].strip(),
                "remoteport": fields[3].strip(),
                "pid": fields[4].strip(),  
                "dbname": fields[5].strip(),
                "username": fields[6].strip(),
                "authmethod": fields[7].strip(),
                "duration": fields[8].strip(),
                "sslversion": fields[9].strip(),  
                "sslcipher": fields[10].strip(),
                "mtu": fields[11].strip(),
                "sslcompression": fields[12].strip(),
                "sslexpansion": fields[13].strip(),
                "iamauthguid": fields[14].strip(),                    
                "application_name": fields[15].strip(),
                "driver_version": fields[16].strip(),
                "os_version": fields[17].strip(),
                "plugin_name": fields[18].strip()
            }
            record["timestamp"] = datetime.datetime.strptime(fields[1], '%a, %d %b %Y %H:%M:%S:%f').timestamp()*1000
            record['account_id'] = keyary[0]
            record['region'] = keyary[2]
            record['cluster_id'] = keyary[3]
            logger.info(f'Record: {record}')
            records.append({'Data': json.dumps(record).encode('utf-8')})
    if records:
        response = firehose.put_record_batch(
            DeliveryStreamName=os.getenv("FIREHOSE_STREAM_NAME"),
            Records=records
        )
        logger.info(f'Response: {json.dumps(response)[:100]}...')
    logger.info(f'{len(records)} of {len(data)} lines delivered.')

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}...')
    for record in event['Records']:
        # Get the bucket name and key for the new file
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        logger.info(f'Processing s3://{bucket}/{key}')
        obj = s3.get_object(Bucket=bucket, Key=unquote(key))
        data = obj['Body'].read()
        logger.info(f'Length of gz file: {len(data)}.')
        logs = gzip.decompress(data).decode()
        items = re.split("\n", logs)
        # Kinesis Firehose每次最多接受500条记录, 因此分批下载日志，每批500行，当返回行数>=500时，继续下载，小于500时表示下载完毕。
        for start in range(0,len(items),500):
            if 'useractivitylog' in key:
                parseUserActivityLog(key, items[start:start+500])
            elif 'connectionlog' in key:
                parseConnectionLog(key, items[start:start+500])
            elif 'userlog' in key:
                parseUserLog(key, items[start:start+500])

