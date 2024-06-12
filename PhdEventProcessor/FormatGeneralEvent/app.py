import os
import json
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontLogsToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    message = json.dumps(event, indent=2)
    if message: 
        event['message'] = message
        event['subjecg'] =【AWS通知】健康事件通知'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    logger.info(f'Event Out: {event}')
    return event

