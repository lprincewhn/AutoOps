import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = ec2 = boto3.client('ec2')
    response = client.describe_volumes(
        VolumeIds=[
            event.get('VolumeId'),
        ],
        DryRun=False
    )
    print(f'Response: {response}')
    for vol in response.get('Volumes'):
        event['Size'] = vol.get('Size')
        break
    event['NewSize'] = event['Size'] + int(os.getenv('SCALING_SIZE', '10'))
    response = client.modify_volume(
        DryRun=False,
        VolumeId=event.get('VolumeId'),
        Size=event.get('NewSize'),
    )    
    print(f'Response: {response}')
    print(f'Ouput: {event}')
    return event
