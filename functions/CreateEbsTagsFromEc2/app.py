import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    print(f'Environment TAGS_TO_SYNC: {os.getenv("TAGS_TO_SYNC")}')
    client = boto3.client('ec2')
    response = client.describe_instances(
        InstanceIds=[
            event.get('InstanceId'),
        ]
    )
    print(f'Response: {response}')
    tags_on_ec2 = response['Reservations'][0]['Instances'][0]['Tags']
    print(f'EC2 tags: {tags_on_ec2}')
    tags_to_sync = list(map(lambda x:x.strip(), os.getenv('TAGS_TO_SYNC').split(',')))
    print(f'Tags to syc: {tags_to_sync}')
    tags = list(filter(lambda x:x.get('Key') in tags_to_sync, tags_on_ec2))
    print(f'EBS tags: {tags}')
    if tags:
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
