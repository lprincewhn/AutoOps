import os
import re
import os
import boto3
import gzip
import json
import datetime
import logging
import IPy

logging.basicConfig()
logger = logging.getLogger("CloudTrailEvents")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

s3 = boto3.client('s3')
eventbridge = boto3.client('events')
authorized_dba = os.getenv('AUTHORIZED_DBA', '').split(',')

def isTrustedIP(ip):
    trusted_ip = os.getenv('TRUSTED_IP', '').split(',')
    for item in trusted_ip:
        if ip in IPy.IP(item.strip()):
            return True
    return False

def isAuthorizedDBA(username):
    authorized_dbas = [x.strip() for x in os.getenv('AUTHORIZED_DBA', '').split(',')]
    return username in authorized_dbas

def isAuthorizedEC2Admin(username):
    authorized_ec2admin = [x.strip() for x in os.getenv('AUTHORIZED_EC2ADMIN', '').split(',')]
    return username in authorized_ec2admin

def checkCloudTrailLog(record):
    logger.debug(f'Item: {record}')
    sourceIPAddress = record['sourceIPAddress']
    userType = record['userIdentity']['type']
    userName = record['userIdentity'].get('userName')
    eventName = record['eventName']
    events = []
    if eventName=='ConsoleLogin' and userType=='Root':
        events.append({
            'Time':datetime.datetime.now(),
            'Source':'AutoOpsCloudTrailEvents',
            'DetailType':'AWS Root account login',
            'Detail':json.dumps(record),
            'EventBusName': os.getenv('EVENT_BUS_NAME')
        })
    if eventName=='ConsoleLogin' and (not isTrustedIP(sourceIPAddress)):
        events.append({
            'Time':datetime.datetime.now(),
            'Source':'AutoOpsCloudTrailEvents',
            'DetailType':'Login from untrusted IP',
            'Detail':json.dumps(record),
            'EventBusName': os.getenv('EVENT_BUS_NAME')
        })
    if (eventName.startswith('CreateDBInstance') or eventName.startswith('DeleteDBInstance')) and (not isAuthorizedDBA(userName)):
        events.append({
            'Time':datetime.datetime.now(),
            'Source':'AutoOpsCloudTrailEvents',
            'DetailType':'Unauthorized user create/delte RDS DB Instance',
            'Detail':json.dumps(record),
            'EventBusName': os.getenv('EVENT_BUS_NAME')
        })
    if eventName=='RunInstances' and (not isAuthorizedEC2Admin(userName)):
        events.append({
            'Time':datetime.datetime.now(),
            'Source':'AutoOpsCloudTrailEvents',
            'DetailType':'Unauthorized user start EC2 Instance',
            'Detail':json.dumps(record),
            'EventBusName': os.getenv('EVENT_BUS_NAME')
        })
    logger.debug(f'Found events: {events}')
    return events

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}...')
    # Get the bucket name and key for the new file
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']
    if '/CloudTrail/' in key:
        logger.info(f'Processing s3://{bucket}/{key}')
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = obj['Body'].read()
        logger.info(f'Length of gz file: {len(data)}.')
        logs = json.loads(gzip.decompress(data).decode())
        events = []
        for r in logs['Records']:
            events += checkCloudTrailLog(r)
        if events:
            response = eventbridge.put_events(
                Entries=events,
            )
            logger.info(f'Response: {json.dumps(response)[:100]}...')
            logger.info(f'{len(events)} events delivered.')

if __name__ == '__main__':
    lambda_handler(None, None)
