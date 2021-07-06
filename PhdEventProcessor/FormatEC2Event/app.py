
import os
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    region = event['region']
    ec2 = boto3.client('ec2', region_name = region)
    alarmName = event["alarmName"]
    timestamp = event["timestamp"]
    instanceId = event["metrics"][0]["metricStat"]["metric"]["dimensions"]["InstanceId"]
    response = ec2.describe_instances(InstanceIds=[instanceId])
    logger.info(f'Response: {response}')
    tags_on_ec2 = response['Reservations'][0]['Instances'][0].get('Tags', [])
    nametag = list(filter(lambda x:x.get('Key')=='Name', tags_on_ec2))
    instanceName = nametag[0].get('Value') if nametag else ''
    message = None
    if 'High-CPUUtilization-Alarm' in alarmName:
        message = f'{timestamp},  AWS区域 {region} EC2 实例"{instanceName}"({instanceId}) CPU使用率过高：{event["reason"]}'
    if 'Failed-SystemStatusCheck-Alarm' in alarmName:
        message = f'{timestamp},  AWS区域 {region} EC2 实例"{instanceName}"({instanceId}) 系统健康检查失败。'
    if 'Failed-InstanceStatusCheck-Alarm' in alarmName:
        message = f'{timestamp},  AWS区域 {region} EC2 实例"{instanceName}"({instanceId}) 实例健康检查失败。'
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】EC2健康事件通知'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    logger.info(f'Event Out: {event}')
    return event

