import os 
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
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
            'DriveLetter': [event['DriveLetter']]
        }
    )
    return event 
