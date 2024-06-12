import os
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    print(f'Event In: {event}')
    account = event['account']
    region = event['region']
    ec2 = boto3.client('ec2', region_name=region)
    instanceId = event["InstanceId"]
    response = ec2.describe_instances(InstanceIds=[instanceId])
    logger.info(f'Response: {response}')
    tags_on_ec2 = response['Reservations'][0]['Instances'][0].get('Tags', [])
    nametag = list(filter(lambda x:x.get('Key')=='Name', tags_on_ec2))
    instanceName = nametag[0].get('Value') if nametag else '-'
    private_ip = response['Reservations'][0]['Instances'][0].get('PrivateIpAddress')
    message = f'''时间: {event['timestamp']}
AWS帐号: {account}
AWS区域：{region}
资源类型：EC2实例
资源名称：{instanceName} ({instanceId}, {private_ip})
事件：EC2实例停止
'''
    receiver = os.getenv('RECEIVER', 'all')
    print(f'SNSTopicArn: {os.getenv("SNSTopicArn")}')
    topicArn = os.getenv("SNSTopicArn")
    topicRegion = topicArn.split(':')[3]
    client = boto3.client('sns',region_name=topicRegion)
    response = client.publish(
        TopicArn=os.getenv('SNSTopicArn'),
        Message=message,
        Subject='【AWS通知】EC2停机',
        MessageAttributes= {"receiver":  {"DataType": "String", "StringValue": receiver}}
    )
    print(response)
    return event
