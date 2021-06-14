import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = ec2 = boto3.client('cloudwatch')
    for volume in event['Volumes']:   
        response = client.put_metric_alarm(
            AlarmName=f'DiskSpace-{event["InstanceId"]}-{volume["instance"]}',
            ActionsEnabled=False,
            MetricName='LogicalDisk % Free Space',
            Namespace='CWAgent',
            Statistic='Average',
            Dimensions=[{
                'Name': 'InstanceId',
                'Value': event['InstanceId']
            },{
                'Name': 'ImageId',
                'Value': event['ImageId']
            },{
                'Name': 'InstanceType',
                'Value': event['InstanceType']
            },{
                'Name': 'instance',
                'Value': f'{volume["instance"]}:' 
            },{
                'Name': 'objectname',
                'Value': 'LogicalDisk'
            }],
            Period=60,
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=int(os.getenv('FREE_THRESHOLD', '20')),
            ComparisonOperator='LessThanOrEqualToThreshold',
            TreatMissingData='missing',
            Tags=[]
        )
    print(f'Response: {response}')
    return event
