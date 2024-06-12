import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = ec2 = boto3.client('cloudwatch')
    response = client.describe_alarms(
        AlarmNamePrefix=f'DiskSpace-{event["InstanceId"]}'
    )
    print(f'Response: {response}')
    response = client.delete_alarms(
        AlarmNames=list(map(lambda x:x.get('AlarmName'), response['MetricAlarms']))
    )
    print(f'Response: {response}')
    return event
