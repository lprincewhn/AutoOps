import os
import json
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    volumeId = event["resourceId"]
    ec2 = boto3.client('ec2')
    response = ec2.describe_volumes(VolumeIds=[volumeId])
    logger.debug(response)
    instanceId = None
    try: 
        instanceId = response['Volumes'][0]['Attachments'][0]['InstanceId']
    except:
        pass
    event['instanceId'] = instanceId
    logger.info(f'Event Out: {event}')
    return event

