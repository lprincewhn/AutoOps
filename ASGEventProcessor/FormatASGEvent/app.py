
import os
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    region = event['region']
    eventType = event["eventType"]
    timestamp = event["timestamp"]
    asgName = event["asgName"]
    instanceId = event["instanceId"]
    cause = event['cause']
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances(InstanceIds=[instanceId])
    logger.info(f'Response: {response}')
    instanceNameStr = ''
    for r in response['Reservations']:
        for i in r['Instances']:
            tags_on_ec2 = i.get('Tags', [])
            nametag = list(filter(lambda x:x.get('Key')=='Name', tags_on_ec2))
            instanceName = nametag[0].get('Value') if nametag else '-'
            instanceNameStr += f'{instanceName} ({i.get("InstanceId")}, {i.get("PrivateIpAddress")}),'
    message = f'''时间: {timestamp}
AWS区域：{region}
资源类型：EC2自动伸缩组(ASG)
资源名称：{asgName}
实例名称：{instanceNameStr[:-1]}
事件：{eventType}
原因：{cause}
'''
    if message:
        event['message'] = message
        event['subject'] = '【AWS通知】EC2自动伸缩组事件通知'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    logger.info(f'Event Out: {event}')
    return event

