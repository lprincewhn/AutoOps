import os
import json
import datetime
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("NotifySns")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    event['subject'] = '【AWS通知】EC2自动伸缩组事件通知'
    event['receiver'] = os.getenv('Receiver', 'all')
    event['message'] = ''

    beijing_time = datetime.datetime.strptime(event["detail"]["StartTime"][:25].strip(), '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    account = event['account']
    region = event['region']
    eventType = event['detail-type']
    asgName = event['detail']['AutoScalingGroupName']
    cause = event['detail']['Cause']
    instanceDetails = event['instanceDetails']
    event['message'] = f'''时间: {beijing_time}
AWS帐号: {account}
AWS区域：{region}
资源类型：EC2自动伸缩组(ASG)
资源名称：{asgName}
实例名称：{instanceDetails}
事件：{eventType}
原因：{cause}
'''
    if event['message']:
        logger.info(f'SNSTopicArn: {os.getenv("SNSTopicArn")}')
        topicArn = os.getenv("SNSTopicArn")
        topicRegion = topicArn.split(':')[3]
        client = boto3.client('sns',region_name=topicRegion)
        response = client.publish(
            TopicArn=os.getenv('SNSTopicArn'),
            Message=event.get('message'),
            Subject=event.get('subject'),
            MessageAttributes= {"receiver":  {"DataType": "String", "StringValue": event.get("receiver", "all")}}
        )
        logger.debug(response)
        event['snsResponse'] = response
    return event
