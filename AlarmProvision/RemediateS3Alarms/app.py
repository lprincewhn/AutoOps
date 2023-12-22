import os
import json
import boto3
import logging
import common

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)


def create5xxRateAlarm(bucketMetricCfg, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    bucketName = bucketMetricCfg["BucketName"]
    metricCfgId = bucketMetricCfg["Id"]
    alarmName = f'AWS/S3-5xxRate-{bucketName}-{metricCfgId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(bucketMetricCfg.get('TagList', []), '5xxRate', 1)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'S3桶{bucketName}, 统计范围{metricCfgId}, 5xx错误率超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/S3',
                        'MetricName': '5xxErrors',
                        'Dimensions': [
                            {
                                'Name': 'BucketName',
                                'Value': bucketName
                            },
                            {
                                'Name': 'FilterId',
                                'Value': metricCfgId
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'Label': '5xxErrors',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/S3',
                        'MetricName': 'AllRequests',
                        'Dimensions': [
                            {
                                'Name': 'BucketName',
                                'Value': bucketName
                            },
                            {
                                'Name': 'FilterId',
                                'Value': metricCfgId
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'Label': 'AllRequests',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1/m2*100',
                'Label': f'{bucketName}-{metricCfgId}',
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=threshold,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    # 获取当前区域所有S3桶
    client = boto3.client('s3')
    response = client.list_buckets()
    bucketList = []
    for bucket in response["Buckets"]:
        response = client.get_bucket_location(Bucket=bucket['Name'])
        bucketLocation = response.get('LocationConstraint') if response.get('LocationConstraint') else 'us-east-1'
        if bucketLocation == os.getenv('AWS_REGION'):
            bucketList.append(bucket)
            
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    paginator = client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/S3-')
    alarmNames = []
    for page in page_iterator:
        alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))

    # 创建告警
    numOfAlarmsCreated = 0
    for bucket in bucketList:
        client = boto3.client('s3')
        response = client.list_bucket_metrics_configurations(Bucket=bucket['Name'])
        metriCfgList = response.get('MetricsConfigurationList', [])
        try:
            response = client.get_bucket_tagging(Bucket=bucket['Name'])
            bucket['TagSet'] = response.get('TagSet', [])
        except:
            bucket['TagSet'] = []
        for metricCfg in metriCfgList:
            metricCfg['BucketName'] = bucket['Name']
            metricCfg['TagList'] = bucket['TagSet']
            print(metricCfg)
            alarmName, created = create5xxRateAlarm(metricCfg, alarmNames)
            numOfAlarmsCreated += 1 if created else 0


    # 删除不再使用的告警
    logger.info(f'Delete orphan alarms: {alarmNames}')
    for x in range(0, len(alarmNames), 100):
        response = client.delete_alarms(
            AlarmNames=alarmNames[x:x+100]
        )

    event["numOfAlarmsCreated"] = event.get("numOfAlarmsCreated", 0) + numOfAlarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmNames
    logger.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})


