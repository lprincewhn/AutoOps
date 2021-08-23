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
    if 'High-IOPS-Alarm' in alarmName:
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：RDS实例
资源名称：{dbInstance}
事件：IOPS超出阈值，对于GP2存储，请考虑增加其容量，对于IO1存储，请考虑增大预置IOPS
详情：{event["reason"]}
'''
    if 'High-Throughput-Alarm' in alarmName:
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：RDS实例
资源名称：{dbInstance}
事件：IO吞吐量超出阈值，请考虑使用吞吐量更大的存储
详情：{event["reason"]}
'''
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】RDS 告警'
        event['receiver'] = 'all'
    print(f'Event Out: {event}')
    return event

