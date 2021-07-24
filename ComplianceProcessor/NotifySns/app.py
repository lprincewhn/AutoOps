import os
import time
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
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
    logger.info(response)
    return event
