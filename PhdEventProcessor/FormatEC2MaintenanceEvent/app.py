
import os
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    region = event['region']
    eventTypeCode = event["eventTypeCode"]
    timestamp = event["timestamp"]
    eventDescription = event["eventDescription"][0]["latestDescription"]
    instanceIds = list(map(lambda x: x.get("entityValue"), event["affectedEntities"]))
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances(InstanceIds=instanceIds)
    logger.info(f'Response: {response}')
    resourceNameStr = ''
    for r in response['Reservations']:
        for i in r['Instances']:
            tags_on_ec2 = i.get('Tags', [])
            nametag = list(filter(lambda x:x.get('Key')=='Name', tags_on_ec2))
            instanceName = nametag[0].get('Value') if nametag else '-'
            resourceNameStr += f'{instanceName} ({i.get("InstanceId")}, {i.get("PrivateIpAddress")}),'
    message = None
    if 'AWS_EC2_INSTANCE_REBOOT_FLEXIBLE_MAINTENANCE_SCHEDULED' in eventTypeCode:
        message = f'''时间: {timestamp}
AWS区域：{region}
资源类型：EC2实例
资源名称：{resourceNameStr[:-1]}
事件：EC2维护重启
详情：EC2实例在维护期间将会不可用并自动重启。如果该实例不带实例存储，你可以在{timestamp}之前手动进行Stop/Start操作，该操作将会使得实例被迁移到健康主机上。{eventDescription}
'''
    if message:
        event['message'] = message
        event['subject'] = '【AWS通知】EC2健康事件通知'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    logger.info(f'Event Out: {event}')
    return event

