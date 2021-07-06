import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    region = os.getenv('AWS_REGION')
    client = boto3.client('cloudwatch')
    response = None
    try:
        response = client.put_metric_alarm(
            AlarmName=f'EC2-{event["InstanceId"]}-Failed-SystemStatusCheck-Alarm',
            AlarmActions=[f'arn:aws:automate:{region}:ec2:recover'],
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
    except:
        response = client.put_metric_alarm(
            AlarmName=f'EC2-{event["InstanceId"]}-Failed-SystemStatusCheck-Alarm',
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
    response = client.put_metric_alarm(
        AlarmName=f'EC2-{event["InstanceId"]}-Failed-InstanceStatusCheck-Alarm',
        MetricName='StatusCheckFailed_Instance',
        Namespace='AWS/EC2',
        Statistic='Average',
        Dimensions=[{
            'Name': 'InstanceId',
            'Value': event['InstanceId']
        }],
        Period=60,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=0,
        ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    return event
