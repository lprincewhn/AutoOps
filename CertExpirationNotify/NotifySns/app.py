import os
import json
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CertExpirationNotify")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    event['subject'] = '【AWS通知】证书过期通知'
    event['receiver'] = os.getenv('Receiver', 'all')
    event['message'] = ''
    
    for certArn in event.get('resources'):
        if int(event.get("daysToExpiry")) > 0:
            event['message'] += f'''证书ARN: {certArn} 将于{int(event.get("daysToExpiry"))}天后过期。
关联资源:
'''
        else:
            event['message'] += f'''证书ARN: {certArn} 已于{-int(event.get("daysToExpiry"))}天前过期。
关联资源:
'''
        for r in event.get('linked_resources').get(certArn):
            event['message'] += f'\t{r["resourceArn"]}'
            if r.get('CNames'):
                event['message'] += f'\t域名: {",".join(r.get("CNames"))}'
            event['message'] += '\n'
        event['message'] += '\n'
    logger.info(f'Message: {event["message"]}')

    if event['message']:
        logger.info(f'SNSTopicArn: {os.getenv("SNSTopicArn")}')
        topicArn = os.getenv("SNSTopicArn")
        topicRegion = topicArn.split(':')[3]
        client = boto3.client('sns',region_name=topicRegion)
        response = client.publish(
            TopicArn=os.getenv('SNSTopicArn'),
            Subject=event.get('subject'),
            MessageAttributes= {'receiver':  {'DataType': 'String', 'StringValue': event.get('receiver', 'all')}},
            Message=event.get('message')
        )
        logger.debug(response)
        event['snsResponse'] = response
    return event
