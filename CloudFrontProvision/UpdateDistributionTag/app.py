import os
import time
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Input: {event}')
    tags = {}
    tags['Items'] = []
    if not event.get('DistributionOwner'):
        logger.info('Tag "Owner" does not exist. Tag it with user name or role name.')
        tags['Items'].append(
            {
                'Key': 'Owner',
                'Value': event['IdentityName']
            }            
        )
    for tag in event.get('IdentityTags'):
        if not tag.get('Key') in event.get('DistributionTagKeys'):
            logger.info(event.get('IdentityName') + " has Tag " + tag.get('Key') + " of " + tag.get('Value'))
            logger.info("Distribution has no Tag " + tag.get('Key') + ". Tag it with " + tag.get('Value'))
            tags["Items"].append(tag)
    client = boto3.client('cloudfront')
    response = client.tag_resource(
        Resource=event['DistributionArn'],
        Tags=tags
    )
    logger.info(f'Response: {response}')
    return event
