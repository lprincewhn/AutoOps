'''
返回值必须是可以JSON序列化的对象，建议仅使用字符串和数值两种类型。如datetime类型不可使用，可将其转换为数值再返回。
'''

import json
import boto3
import botocore
import datetime
import string

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('ec2')
    response = client.describe_instances(
        InstanceIds=[
            event['InstanceId'],
        ]
    )
    print(f'Response: {response}')
    event['ImageId'] = response['Reservations'][0]['Instances'][0]['ImageId']
    event['InstanceType'] = response['Reservations'][0]['Instances'][0]['InstanceType']
    return event
