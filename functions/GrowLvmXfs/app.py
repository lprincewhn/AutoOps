import os
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    pvname = event['device']
    lvname = event['DeviceName'] + event['PartitionNum']
    client = boto3.client('ssm')
    response = client.send_command(
        InstanceIds=[
            event.get('InstanceId'),
        ],
        DocumentName=os.getenv('SSM_DOCNAME'),
        DocumentVersion='$DEFAULT',
        TimeoutSeconds=30,
        Comment=event.get('Comment', ''),
        Parameters={
            'PVName': [pvname],
            'LVName': [lvname]
        }
    )
    return event 
