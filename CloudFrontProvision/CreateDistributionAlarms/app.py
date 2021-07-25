import os
import json
import boto3
import logging

logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    client = ec2 = boto3.client('cloudwatch')
    response = client.put_metric_alarm(
        AlarmName=f'CloudFront-{event["DistributionId"]}-High-5xxErrorRate-Alarm',
        ActionsEnabled=False,
        MetricName='5xxErrorRate',
        Namespace='AWS/CloudFront',
        Statistic='Average',
        Dimensions=[{
            'Name': 'Region',
            'Value': 'Global'
        },{
            'Name': 'DistributionId',
            'Value': event["DistributionId"] 
        }],
        Period=300,
        EvaluationPeriods=2,
        DatapointsToAlarm=2,
        Threshold=5,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    logger.info(f'Response: {response}')
    response = client.put_metric_alarm(
        AlarmName=f'CloudFront-{event["DistributionId"]}-High-OriginBandwidth-Alarm',
        ActionsEnabled=False,
        Metrics=[{
            'Id': 'origin_bandwidth',
            'Expression': 'byte_downloaded*(100-cache_hit_rate)/100*8/PERIOD(byte_downloaded)',
            'Label': 'OriginBandwidth(bps)',
            'ReturnData': True
        },{
            'Id': 'byte_downloaded',
            'MetricStat': {
            	'Metric': {
                    'Namespace': 'AWS/CloudFront',
                    'MetricName': 'BytesDownloaded',
                    'Dimensions': [{
                        'Name': 'Region',
                        'Value': 'Global'
                    },{
                        'Name': 'DistributionId',
                        'Value': event["DistributionId"]
                    }]
                },
                'Period': 300,
                'Stat': 'Sum' 
            },
            'Label': 'BytesDownloaded',
            'ReturnData': False 
        },{
            'Id': 'cache_hit_rate',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/CloudFront',
                    'MetricName': 'CacheHitRate',
                    'Dimensions': [{
                        'Name': 'Region',
                        'Value': 'Global'
                    },{
                        'Name': 'DistributionId',
                        'Value': event["DistributionId"]
                    }]
                },
                'Period': 300,
                'Stat': 'Average'
            },
            'Label': 'CacheHitRate',
            'ReturnData': False
        }],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1500000000,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    logger.info(f'Response: {response}')
    response = client.put_metric_alarm(
        AlarmName=f'CloudFront-{event["DistributionId"]}-High-Requests-Alarm',
        ActionsEnabled=False,
        MetricName='Requests',
        Namespace='AWS/CloudFront',
        Statistic='Sum',
        Dimensions=[{
            'Name': 'Region',
            'Value': 'Global'
        },{
            'Name': 'DistributionId',
            'Value': event["DistributionId"]
        }],
        Period=300,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1800000000,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    logger.info(f'Response: {response}')
    response = client.put_metric_alarm(
        AlarmName=f'CloudFront-{event["DistributionId"]}-Low-RequestsChangeRate-Alarm',
        ActionsEnabled=False,
        Metrics=[{
            'Id': 'request_change_rate',
            'Expression': 'last_requests/llast_requests-1',
            'Label': 'RequestsChangeRate',
            'ReturnData': True
        },{
            'Id': 'llast_requests',
            'Expression': 'last_requests-RATE(last_requests)*PERIOD(requests)',
            'Label': 'LastLastRequests',
            'ReturnData': False 
        },{
            'Id': 'last_requests',
            'Expression': 'requests-RATE(requests)*PERIOD(requests)',
            'Label': 'LastRequests',
            'ReturnData': False
        },{
            'Id': 'requests',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/CloudFront',
                    'MetricName': 'Requests',
                    'Dimensions': [{
                        'Name': 'Region',
                        'Value': 'Global'
                    },{
                        'Name': 'DistributionId',
                        'Value': event["DistributionId"]
                    }]
                },
                'Period': 300,
                'Stat': 'Sum'
            },
            'Label': 'Requests',
            'ReturnData': False
        }],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=-0.8,
        ComparisonOperator='LessThanThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    logger.info(f'Response: {response}')
    return event
