import os
import json
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Input: {json.dumps(event)}')
    event['instanceId'] = event.get('detail').get('responseElements').get('instanceId')
    event['volumeId'] = event.get('detail').get('responseElements').get('volumeId')
    client = boto3.client('ec2')
    response = client.describe_volumes(
        VolumeIds=[event['volumeId']],
    )
    logger.debug(f'Response: {response}')
    attachements = response['Volumes'][0]['Attachments']
    event['volumeType'] = response['Volumes'][0]['VolumeType']
    event['iops'] = response['Volumes'][0]['Iops']
    event['throughput'] = response['Volumes'][0]['Throughput']
    event['size'] = response['Volumes'][0]['Size']
    if event.get('detail').get('eventName').startswith('Attach'): 
        if len(attachements)>1: 
            event['operation'] = 'reattach'
        else:
            event['operation'] = 'attach'
    if event.get('detail').get('eventName').startswith('Detach'):
        if len(attachements)>1:
            event['operation'] = 'detach'
        else:
            event['operation'] = 'detachlast'
 
    return event
