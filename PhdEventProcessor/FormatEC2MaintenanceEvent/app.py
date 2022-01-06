import os
import json
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    account = event['account']
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
    message = json.dumps(event, indent=2)
    if 'AWS_EC2_INSTANCE_REBOOT_FLEXIBLE_MAINTENANCE_SCHEDULED' in eventTypeCode:
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：EC2实例
资源名称：{resourceNameStr[:-1]}
事件：EC2维护重启
详情：EC2实例在维护期间将会不可用并自动重启。如果该实例不带实例存储，你可以在{timestamp}之前手动进行Stop/Start操作，该操作将会使得实例被迁移到健康主机上。如果该实例带实例存储，Stop/Start操作将使得实例存储中的数据丢失，请谨慎操作。通过以下链接可查看事件列表和修改维护窗口 https://{region}.console.aws.amazon.com/ec2/v2/home?region={region}#Events: 
'''
    if 'AWS_EC2_PERSISTENT_INSTANCE_RETIREMENT_SCHEDULED' in eventTypeCode:
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：EC2实例
资源名称：{resourceNameStr[:-1]}
事件：EC2主机退服
详情：退服后EC2实例将进入Stop状态。如果该实例不带实例存储，你可以在{timestamp}之前手动进行Stop/Start操作，该操作将会使得实例被迁移到健康主机上。如果该实例带实例存储，退役后或Stop/Start操作均将使得实例存储中的数据丢失，请及时备份。通过以下链接可查看事件列表和修改维护窗口 https://{region}.console.aws.amazon.com/ec2/v2/home?region={region}#Events: 
'''
    if message:
        event['message'] = message
        event['subject'] = '【AWS通知】健康事件通知'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    logger.info(f'Event Out: {event}')
    return event

