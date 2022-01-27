import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('cloudwatch')
    response = client.put_metric_alarm(
        AlarmName=f'EC2-{event["InstanceId"]}-High-Memory-Alarm',
        ActionsEnabled=False,
        MetricName='mem_used_percent',
        Namespace='CWAgent',
        Statistic='Average',
        Dimensions=[{
            'Name': 'AutoScalingGroupName',
            'Value': event['AutoScalingGroupName']
        },{
            'Name': 'InstanceId',
            'Value': event['InstanceId']
        },{
            'Name': 'ImageId',
            'Value': event['ImageId']
        },{
            'Name': 'InstanceType',
            'Value': event['InstanceType']
        }],
        Period=300,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=int(os.getenv('MEMORY_THRESHOLD', '80')),
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    return event
