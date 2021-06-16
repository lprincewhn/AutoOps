import json
import boto3
import datetime
import time

    
def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["alarmName"]
    timestamp = event["timestamp"]
    alarmValue = event["alarmValue"]
    dbInstance = event["metrics"][0]["metricStat"]["metric"]["dimensions"]["DBInstanceIdentifier"]
    message = None
    if 'Low-EBSIOBalance-Alarm' in alarmName:
        message = f'{timestamp},  AWS RDS 数据库节点 {dbInstance} EBS IO 积分不足。'
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】RDS 告警'
        event['receiver'] = 'all'
    print(f'Event Out: {event}')
    return event

