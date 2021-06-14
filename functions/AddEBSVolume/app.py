import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Event In: {event}')
    client = ec2 = boto3.client('ec2')
    response = client.describe_instances(
        InstanceIds=[
            evnet.get('InstanceId'),
        ],
    )
    print(f'Response: {response}')
    event['AvailabilityZone'] = response['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone'] 
    deviceMappings = response['Reservations'][0]['Instances'][0]['BlockDeviceMappings']
    event['DeviceNames'] = list(map(lambda x:x['DeviceName'], deviceMappings))
    if len(event['DeviceNames'])>=10:
        raise Except('Too many volumes')
    response = client.create_volume(
        AvailabilityZone=event['AvailabilityZone'],
        Iops=3000,
        Size=os.getenv('Size', 1),
        VolumeType='gp3'
    )
    print(f'Response: {response}')
    event['VolumeId'] = response['VolumeId']
    lastDevice = max(event['DeviceNames'])
    if chr(ord(lastName[-1])+1) > 'z':
        raise Except('Cannot assgin deivce Name')
    event['newDeviceName'] = lastName[:-1] + chr(ord(lastName[-1])+1)
    response = client.attach_volume(
        Device=event['newDeviceName'],
        InstanceId=evnet.get('InstanceId'),
        VolumeId=event['VolumeId'],
    )
    print(f'Response: {response}')
    print(f'Event Out: {event}')
    return event
