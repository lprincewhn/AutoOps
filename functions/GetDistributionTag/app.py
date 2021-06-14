import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('cloudfront')
    response = client.list_tags_for_resource(
        Resource=event.get("DistributionArn")
    )
    print(f'Response: {response}')
    distribution_project_tag = list(filter(lambda x:x.get('Key')=='Project', response['Tags'].get('Items', [])))
    distribution_owner_tag = list(filter(lambda x:x.get('Key')=='Owner', response['Tags'].get('Items', [])))
    event['DistributionProject'] = distribution_project_tag[0]['Value'] if distribution_project_tag else ''
    event['DistributionOwner'] = distribution_owner_tag[0]['Value'] if distribution_owner_tag else '' 
    return event
