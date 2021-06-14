import os
import sys
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = ec2 = boto3.client('cloudwatch')
    response = client.put_metric_alarm(
        AlarmName=f'EC2-{event["InstanceId"]}-HighCPU',
        ActionsEnabled=False,
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Statistic='Average',
        Dimensions=[{
            'Name': 'InstanceId',
            'Value': event['InstanceId']
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=int(os.getenv('CPU_THRESHOLD', '80')),
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    return event

if __name__ == '__main__':
   event = {'InstanceId': sys.argv[1]}
   lambda_handler(event, None)
