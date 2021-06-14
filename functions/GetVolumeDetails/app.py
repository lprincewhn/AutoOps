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
    client = ec2 = boto3.client('ec2')
    response = None
    try:
        response = client.describe_volumes_modifications(
            VolumeIds=[
                event.get('VolumeId'),
            ],
            DryRun=False
        )   
    except botocore.exceptions.ClientError as error:
        print(f'Error: {error}')
        if error.response['Error']['Code'] == 'InvalidVolumeModification.NotFound':
            event['ModificationState'] = 'completed'
            event['canModifyVolume'] = 'true'
            print(f'Ouput: {event}')
            return event
    print(f'Response: {response}')
    for vol in response.get('VolumesModifications'):
        event['ModificationState'] = vol.get('ModificationState')
        if datetime.datetime.now().timestamp() < vol.get('StartTime').timestamp() + 24 * 3600:
            event['canModifyVolume'] = 'false'
        else:
            event['canModifyVolume'] = 'true'
        print(f'Ouput: {event}')
        return event
    raise Exception('Cannot get volume details')
