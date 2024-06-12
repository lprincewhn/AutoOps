import os
import json
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("RDSProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    client = boto3.client('rds')
    response = client.modify_db_instance(
        DBInstanceIdentifier=event.get('dbInstanceIdentifier'),
        CloudwatchLogsExportConfiguration={
            'EnableLogTypes': [
                'string',
            ],
            'DisableLogTypes': [
                'string',
            ]
        }
    )
    logger.debug(f'Response: {response}')
    client = boto3.client('logs')
    response = client.put_metric_filter(
        logGroupName=f'/aws/rds/cluster/{event.get("dbInstanceIdentifier")}/general',
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
    logger.debug(f'Response: {response}')
    client = boto3.client('cloudwatch')
    response = client.put_metric_alarm(
        AlarmName=f'RDS-{event.get("dbInstanceIdentifier")}-High-InsertCount-Alarm',
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
