import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = ec2 = boto3.client('ssm')
    response = client.describe_instance_information(
        Filters=[
            {
                'Key': 'InstanceIds',
                'Values': [
                    event['InstanceId']
                ]
            }
        ]
    )  
    print(f'Response: {response}')
    event['PingStatus'] = response['InstanceInformationList'][0]['PingStatus'] if response['InstanceInformationList'] else ''
    event['PlatformType'] = response['InstanceInformationList'][0]['PlatformType'] if response['InstanceInformationList'] else ''
    print(f'Ouput: {event}')
    return event
