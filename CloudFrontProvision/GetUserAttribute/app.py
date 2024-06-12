import os
import time
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('iam')
    response = client.list_user_tags(
        UserName=event.get('IdentityName')
    )
    print(f'Response: {response}')
    tags_to_sync = os.getenv('TAGS_TO_SYNC').split(',')
    tags = list(filter(lambda x:x.get('Key') in tags_to_sync, response.get('Tags', [])))
    event['IdentityTags'] = tags
    return event
