import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('cloudwatch')
    response = client.put_metric_alarm(
        AlarmName=f'EC2-{event["InstanceId"]}-Failed-SystemStatusCheck-Alarm',
        AlarmActions=['arn:aws:automate:us-east-1:ec2:recover'],
        MetricName='StatusCheckFailed_System',
        Namespace='AWS/EC2',
        Statistic='Average',
        Dimensions=[{
            'Name': 'InstanceId',
            'Value': event['InstanceId']
        }],
        Period=60,
        EvaluationPeriods=2,
        DatapointsToAlarm=2,
        Threshold=0,
        ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    return event
