import os
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    tag_key = os.getenv('TAG_KEY', 'Project')
    logger.info(f"TAG_KEY: {tag_key}")
    client = boto3.client('resourcegroupstaggingapi')
    pagination_token = 'first'
    tag_values = []
    while pagination_token:
        response = client.get_tag_values(
            PaginationToken='' if pagination_token=='first' else pagination_token,
            Key=tag_key
        )
        logger.info(response)
        tag_values += response['TagValues']
        pagination_token = response['PaginationToken']
    logger.info(f'Found {len(tag_values)} values of {tag_key}')

    client = boto3.client('resource-groups')
    for tag_value in tag_values:
        try:
            query = f'{{"ResourceTypeFilters": ["AWS::AllSupported"], "TagFilters":[{{"Key": "{tag_key}", "Values":["{tag_value}"]}}]}}'
            response = client.create_group(
                Name=tag_value,
                Description=f'{tag_key}-{tag_value}',
                ResourceQuery={
                    'Type': 'TAG_FILTERS_1_0',
                    'Query': query 
                }
            )
            logger.info(response)
        except Exception as e:
            logger.warn(f"Cannot create resource group {tag_value}. Reason: {e}")

