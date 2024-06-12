import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('iam')
    response = client.list_role_tags(
        RoleName=event.get('IdentityName')
    )
    print(f'Response: {response}')
    role_project_tag = list(filter(lambda x:x.get('Key')=='Project', response.get('Tags', []))) 
    event['IdentityProject'] = role_project_tag[0]['Value'] if role_project_tag else ''
    return event
