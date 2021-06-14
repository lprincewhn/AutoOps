import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('cloudwatch')
    response = client.put_metric_alarm(
        AlarmName=f'EC2-{event["InstanceId"]}-High-CPUUtilization-Alarm',
        ActionsEnabled=False,
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Statistic='Average',
        Dimensions=[{
            'Name': 'InstanceId',
            'Value': event['InstanceId']
        }],
        Period=300,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=int(os.getenv('CPU_THRESHOLD', '80')),
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    return event
