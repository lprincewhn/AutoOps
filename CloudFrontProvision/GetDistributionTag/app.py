import os
import time
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Input: {event}')
    client = boto3.client('cloudfront')
    response = client.get_distribution_config(
        Id=event.get("DistributionId")
    )
    logger.info(f'Response: {response}')
    response = client.list_tags_for_resource(
        Resource=event.get("DistributionArn")
    )
    logger.info(f'Response: {response}')
    tags_to_sync = os.getenv('TAGS_TO_SYNC').split(',')
    tags = list(filter(lambda x:x.get('Key') in tags_to_sync and x.get('Value').strip(), response['Tags'].get('Items', [])))
    distribution_owner_tag = list(filter(lambda x:x.get('Key')=='Owner', response['Tags'].get('Items', [])))
    event['DistributionTagKeys'] =  list(map(lambda x:x.get('Key'), tags))
    event['DistributionOwner'] = distribution_owner_tag[0]['Value'] if distribution_owner_tag else '' 
    return event
