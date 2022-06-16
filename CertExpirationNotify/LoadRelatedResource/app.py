import os
import json
import boto3
import logging
import traceback

logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    resources = event.get('resources')
    daysToExpiry = event.get('detail').get('DaysToExpiry')
    client = boto3.client('acm')
    event['linked_resources'] = {}
    for certArn in resources:
        response = client.describe_certificate(
            CertificateArn = certArn
        )
        logger.debug(f'Response: {response}')
        in_use_by = response['Certificate']['InUseBy']
        cloudfront = boto3.client('cloudfront')
        linked_resources = []
        for r in in_use_by:
            try:
                if 'cloudfront' in r:
                    id = r.split('/')[-1]
                    response = cloudfront.get_distribution_config(
                        Id=id
                    )
                    logger.debug(f'Response: {response}')
                    cnames =  response['DistributionConfig']['Aliases']['Items']
                    linked_resources.append({'resourceArn': r, 'CNames': cnames})    
                else:
                    linked_resources.append({'resourceArn': r})
            except Exception as e:
                traceback.print_exc()
        event['linked_resources'][certArn] = linked_resources
    event['daysToExpiry'] = daysToExpiry
    return event 
