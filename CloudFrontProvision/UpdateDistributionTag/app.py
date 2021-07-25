import os
import time
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Input: {event}')
    tags = {
        'Items': [
            {
                'Key': 'DomainName',
                'Value': event['DomainName']
            }
        ]        
    }
    if not event.get('DistributionOwner'):
        logger.info('Tag "Owner" does not exist. Tag it with user name or role name.')
        tags["Items"].append(
            {
                'Key': 'Owner',
                'Value': event['IdentityName']
            }            
        )

    if (not event.get('DistributionProject')) and event.get('IdentityProject'):
        logger.info(event.get('IdentityName') + " has Project Tag of " + event.get('IdentityProject'))
        logger.info("Distribution has no Tag 'Project'. Tag it with user's project tag.")
        tags["Items"].append(
            {
                'Key': 'Project',
                'Value': event['IdentityProject']
            }            
        )
    client = boto3.client('cloudfront')
    response = client.tag_resource(
        Resource=event['DistributionArn'],
        Tags=tags
    )
    logger.info(f'Response: {response}')
    return event
