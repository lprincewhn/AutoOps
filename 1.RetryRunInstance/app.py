import os
import sys
import json
import boto3
import time
import logging
import datetime


logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    client = boto3.client('ec2')
    response = client.describe_instances(
        Filters=[
            {
                'Name': 'tag:AutoOpsRetyRunInstance',
                'Values': [
                    '1',
                ]
            },
            {
                'Name': 'instance-state-name',
                'Values': [
                    'pending','running','shutting-down','stopping','stopped',
                ]
            },
        ],
    )
    cnt = sum(map(lambda x:len(x["Instances"]), response["Reservations"]))
    logger.info(f'Already has started {cnt} instances')
    needed = int(os.getenv("InstanceCount", "1"))
    if cnt >= needed:
        return cnt
    logger.info(f'Need {needed}. Starting {needed-cnt} new instance.')
    response = client.run_instances(
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeType': 'gp3',
                    'VolumeSize': 8
                },
            },
            {
                'DeviceName': '/dev/sdb',
                'NoDevice': '',
            },
            {
                'DeviceName': '/dev/sdf',
                'NoDevice': '',
            },
        ],
        ImageId=os.getenv('ImageId'),
        InstanceType=os.getenv('InstanceType'),
        KeyName=os.getenv('KeyName'),
        MaxCount=needed-cnt,
        MinCount=1,
        SecurityGroupIds=os.getenv('SecurityGroupIds').split(','),
        SubnetId=os.getenv('SubnetId'),
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'AutoOpsRetyRunInstance',
                        'Value': '1'
                    },
                ]
            },
        ],
    )
    
    if os.getenv('EventBusName'):
        eventbridge = boto3.client('events')
        events = [{
            'Source':'AutoOpsRetryRunInstance',
            'DetailType':'Successfully start EC2 instance',
            'Detail':json.dumps(response, sort_keys=True, default=str),
            'EventBusName': os.getenv('EventBusName')
        }]
        response = eventbridge.put_events(
            Entries=events,
        )
    return cnt+1
    
if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    while True:
        try:
            lambda_handler(None, None)
        except:
            pass
        time.sleep(1)