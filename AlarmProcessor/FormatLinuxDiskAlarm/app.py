import json
import boto3
import datetime
import time

    
def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["alarmName"]
    timestamp = event["timestamp"]
    alarmValue = event["alarmValue"]
    message = json.dumps(event) 
    if message: 
        event['message'] = message
        event['receiver'] = 'all'
        event['subject'] = '【AWS通知】EC2磁盘空间告警'
        event['wait'] = 'wait'
    print(f'Event Out: {event}')
    return event

