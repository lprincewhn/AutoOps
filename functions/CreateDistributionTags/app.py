import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('ec2')
    response = client.describe_instances(
        InstanceIds=[
            event.get('InstanceId'),
        ]
    )
    print(f'Response: {response}')
    tags = response['Reservations'][0]['Instances'][0]['Tags']
    deviceMappings = response['Reservations'][0]['Instances'][0]['BlockDeviceMappings']
    ebsIds = list(map(lambda m: m['Ebs']['VolumeId'], filter(lambda m: m.get('Ebs'), deviceMappings)))
    response = client.create_tags(
        Resources=ebsIds,
        Tags=tags
    )
    print(f'Response: {response}')
    event['Tags']=tags
    event['EbsIds']=ebsIds     
    return event
