import json
import boto3
import datetime
import time

    
def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["alarmName"]
    timestamp = event["timestamp"]
    alarmValue = event["alarmValue"]
    instanceId = event["metrics"][0]["metricStat"]["metric"]["dimensions"]["InstanceId"]
    message = None
    if 'High-CPUUtilization-Alarm' in alarmName:
        message = f'{timestamp},  AWS EC2 实例 {instanceId} CPU使用率过高：{event["reason"]}'
    if 'Failed-SystemStatusCheck-Alarm' in alarmName:
        message = f'{timestamp},  AWS EC2 实例 {instanceId} 系统健康检查失败。'
    if 'Failed-InstanceStatusCheck-Alarm' in alarmName:
        message = f'{timestamp},  AWS EC2 实例 {instanceId} 实例健康检查失败。'
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】ElasticSearch告警'
    print(f'Event Out: {event}')
    return event

