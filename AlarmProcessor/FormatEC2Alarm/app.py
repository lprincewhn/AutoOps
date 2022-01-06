
import os
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    account = event['account']
    region = event['region']
    ec2 = boto3.client('ec2', region_name=region)
    alarmName = event["alarmName"]
    currentState = event["currentState"]
    timestamp = event["timestamp"]
    instanceId = event["metrics"][0]["metricStat"]["metric"]["dimensions"]["InstanceId"]
    response = ec2.describe_instances(InstanceIds=[instanceId])
    logger.info(f'Response: {response}')
    tags_on_ec2 = response['Reservations'][0]['Instances'][0].get('Tags', [])
    nametag = list(filter(lambda x:x.get('Key')=='Name', tags_on_ec2))
    instanceName = nametag[0].get('Value') if nametag else '-'
    private_ip = response['Reservations'][0]['Instances'][0].get('PrivateIpAddress')
    message = None
    if 'High-CPUUtilization-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：EC2实例
资源名称：{instanceName} ({instanceId}, {private_ip})
事件：CPU使用率过高
详情：{event["reason"]}
'''
    if 'Failed-SystemStatusCheck-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：EC2实例
资源名称：{instanceName} ({instanceId}, {private_ip})
事件：系统健康检查失败（底层硬件故障）
详情：将启动自动恢复流程，实例将被停止并在健康的宿主机上重启。如果该实例上的应用在系统启动时不会自动启动，则你需要登录到系统中手动完成。
'''
    if 'Failed-InstanceStatusCheck-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：EC2实例
资源名称：{instanceName} ({instanceId}, {private_ip})
事件：实例健康检查失败（操作系统故障）
'''
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】EC2告警'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    logger.info(f'Event Out: {event}')
    return event

