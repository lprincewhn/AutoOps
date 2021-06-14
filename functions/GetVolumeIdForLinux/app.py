import json
import boto3
import string

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = ec2 = boto3.client('ec2')
    response = client.describe_instance_attribute(
        Attribute='blockDeviceMapping',
        DryRun=False,
        InstanceId=event.get('InstanceId')
    )
    print(f'Response: {response}')
    for item in response.get('BlockDeviceMappings'):
        if item.get('DeviceName').startswith('/dev/') and item.get('DeviceName').rstrip(string.digits)[-1] == event.get('device').rstrip(string.digits)[-1]:
            event['VolumeId'] = item.get('Ebs').get('VolumeId')
            print(f'Ouput: {event}')
            return event
    raise Exception('Cannot find VolumeId')
