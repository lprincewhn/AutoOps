import os
import boto3

def lambda_handler(event, context):
    print(f'Event In: {event}')
    client = ec2 = boto3.client('cloudwatch')
    dbInstanceIdentifier = event["dbInstanceIdentifier"]
    response = client.put_metric_alarm(
        AlarmName=f'RDS-{dbInstanceIdentifier}-Low-EBSIOBalance-Alarm',
        ActionsEnabled=False,
        MetricName='EBSIOBalance%',
        Namespace='AWS/RDS',
        Statistic='Average',
        Dimensions=[{
            'Name': 'DBInstanceIdentifier',
            'Value': dbInstanceIdentifier
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=20,
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
