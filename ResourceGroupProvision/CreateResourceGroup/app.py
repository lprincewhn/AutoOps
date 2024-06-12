import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    logging.info(f'Environment TAG_KEYS: {os.getenv("TAG_KEYS")}')
    tag_keys = os.getenv('TAG_KEYS', 'Project').split(',')
    for tag_key in tag_keys:
        tag_key = tag_key.strip()
        logging.info(f"TAG_KEY: {tag_key}")
        client = boto3.client('resourcegroupstaggingapi')
        paginator = client.get_paginator('get_tag_values')
        page_iterator = paginator.paginate(Key=tag_key)
        tag_values = []
        for page in page_iterator:
            for t in page["TagValues"]:
                tag_values.append(t)
        logging.info(f'Found {len(tag_values)} values of {tag_key}')

        client = boto3.client('resource-groups')
        for tag_value in tag_values:
            if tag_value:
                try:
                    query = f'{{"ResourceTypeFilters": ["AWS::AllSupported"], "TagFilters":[{{"Key": "{tag_key}", "Values":["{tag_value}"]}}]}}'
                    response = client.create_group(
                        Name=f'{tag_key}-{tag_value}',
                        Description=f'Created by tag key AutoOpsResourceGroupProvision',
                        ResourceQuery={
                            'Type': 'TAG_FILTERS_1_0',
                            'Query': query 
                        }
                    )
                    logging.debug(response)
                    event["CreatedResourceGroups"] = event.get("CreatedResourceGroups", []) + [f'{tag_key}-{tag_value}']
                except Exception as e:
                    logging.warning(f"Cannot create resource group {tag_value}. Reason: {e}")
    logging.info(f'Event Out: {json.dumps(event)}')
    return event
if __name__ == '__main__':
    lambda_handler({}, {})