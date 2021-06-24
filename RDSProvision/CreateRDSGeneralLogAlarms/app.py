import os
import boto3

def lambda_handler(event, context):
    print(f'Event In: {event}')
    client = boto3.client('logs')
    response = client.put_metric_filter(
        logGroupName='/aws/rds/cluster/database-1/general',
        filterName='InsertCount',
        filterPattern='"INSERT INTO"',
        metricTransformations=[
            {
                'metricName': 'InsertCount',
                'metricNamespace': 'RDS_GENERAL_LOG',
                'metricValue': '1',
            }
        ]
    )
    print(f'Response: {response}')
    client = ec2 = boto3.client('cloudwatch')
    response = client.put_metric_alarm(
        AlarmName=f'RDS-database-1-High-InsertCount-Alarm',
        ActionsEnabled=False,
        MetricName='InsertCount',
        Namespace='RDS_GENERAL_LOG',
        Statistic='Sum',
        Dimensions=[],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=20,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')

if __name__ == '__main__':
    lambda_handler(None, None)
