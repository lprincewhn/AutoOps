import os
import json
import boto3
import datetime
import logging

logging.basicConfig()
logger = logging.getLogger("LoadInstance")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    region = event['region']
    instanceId = event['detail']['EC2InstanceId']
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances(InstanceIds=[instanceId])
    logger.info(f'Response: {response}')
    instanceDetails = ''
    for r in response['Reservations']:
        for i in r['Instances']:
            tags_on_ec2 = i.get('Tags', [])
            nametag = list(filter(lambda x:x.get('Key')=='Name', tags_on_ec2))
            instanceName = nametag[0].get('Value') if nametag else '-'
            instanceDetails += f'{instanceName} ({i.get("InstanceId")}, {i.get("PrivateIpAddress")}),'

    event['instanceDetails'] = instanceDetails[:-1]
    logger.info(f'Event Out: {json.dumps(event)}')
    return event
