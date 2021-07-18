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
    alarmValue = event["alarmValue"]
    dbInstance = event["metrics"][0]["metricStat"]["metric"]["dimensions"]["DBInstanceIdentifier"]
    message = None
    if 'Low-EBSIOBalance-Alarm' in alarmName:
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：RDS实例
资源名称：{dbInstance}
事件：EBS IO 积分不足
详情：{event["reason"]}
'''
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】RDS 告警'
        event['receiver'] = 'all'
    print(f'Event Out: {event}')
    return event

