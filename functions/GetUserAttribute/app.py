import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('iam')
    response = client.list_user_tags(
        UserName=event.get('IdentityName')
    )
    print(f'Response: {response}')
    user_project_tag = list(filter(lambda x:x.get('Key')=='Project', response.get('Tags', [])))
    event['IdentityProject'] = user_project_tag[0]['Value'] if user_project_tag else '' 
    return event
