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
    aliases = response["DistributionConfig"]["Aliases"].get("Items", [])
    aliases.sort()
    event["DomainName"] = '/'.join(aliases)
    response = client.list_tags_for_resource(
        Resource=event.get("DistributionArn")
    )
    logger.info(f'Response: {response}')
    distribution_project_tag = list(filter(lambda x:x.get('Key')=='Project', response['Tags'].get('Items', [])))
    distribution_owner_tag = list(filter(lambda x:x.get('Key')=='Owner', response['Tags'].get('Items', [])))
    event['DistributionProject'] = distribution_project_tag[0]['Value'] if distribution_project_tag else ''
    event['DistributionOwner'] = distribution_owner_tag[0]['Value'] if distribution_owner_tag else '' 
    return event
