import os
import json
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Input: {json.dumps(event)}')
    print(f'Environment TAGS_TO_SYNC: {os.getenv("TAGS_TO_SYNC")}')
    client = boto3.client('ec2')
    response = client.describe_instances(
        InstanceIds=[
            event.get('instanceId'),
        ]
    )
    logger.debug(f'Response: {response}')
    tags_on_ec2 = response['Reservations'][0]['Instances'][0].get('Tags', [])
    logger.info(f'EC2 tags: {tags_on_ec2}')
    tags_to_sync = list(map(lambda x:x.strip(), os.getenv('TAGS_TO_SYNC').split(',')))
    logger.info(f'Tags to syc: {tags_to_sync}')
    tags = list(filter(lambda x:x.get('Key') in tags_to_sync, tags_on_ec2))
    logger.info(f'EBS tags: {tags}')
    if tags:
        response = client.create_tags(
            Resources=[event.get('volumeId')],
            Tags=tags
        )
        logger.debug(f'Response: {response}')
        event['tags']=tags
    return event
