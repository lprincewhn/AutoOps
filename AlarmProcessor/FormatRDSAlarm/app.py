import os
import json
import boto3
import datetime
import time

    
def lambda_handler(event, context):
    print(f'Event In: {event}')
    account = event['account']
    region = event['region']
    alarmName = event["alarmName"]
    timestamp = event["timestamp"]
    alarmValue = event.get("alarmValue")
    dbInstance = event["metrics"][0]["metricStat"]["metric"]["dimensions"]["DBInstanceIdentifier"]
    message = None
    if event['currentState'] == 'ALARM':
        message = event['eventData']
    if event['previousState'] == 'ALARM' and event['currentState'] == 'OK': 
        message = event['eventData']
    if message: 
        eventOut = {
            'message': message,
            'receiver': 'cmdb',
            'subject': '【AWS通知】RDS 告警'
        }
        if not eventOut.get('receiver'):
            eventOut['receiver'] = os.getenv('RECEIVER', 'all')
    print(f'Event Out: {event}')
    return eventOut

