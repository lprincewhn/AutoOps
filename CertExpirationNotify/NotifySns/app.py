import os
import json
import boto3
import logging

logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)


def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
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
    logging.info(f'Message: {event["message"]}')

    if event['message']:
        logging.info(f'SNSTopicArn: {os.getenv("SNSTopicArn")}')
        topicArn = os.getenv("SNSTopicArn")
        topicRegion = topicArn.split(':')[3]
        client = boto3.client('sns',region_name=topicRegion)
        response = client.publish(
            TopicArn=os.getenv('SNSTopicArn'),
            Subject=event.get('subject'),
            MessageAttributes= {'receiver':  {'DataType': 'String', 'StringValue': event.get('receiver', 'all')}},
            Message=event.get('message')
        )
        event['snsResponse'] = response
    logging.info(f'Event Out: {json.dumps(event)}')
    return event
