import os
import time
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
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
    client = boto3.client('cloudfront')
    response = client.tag_resource(
        Resource=event['DistributionArn'],
        Tags=tags
    )
    logger.info(f'Response: {response}')
    return event
