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
sts = boto3.client('sts')
account_id = sts.get_caller_identity()['Account']


def create5xxRateAlarm(region, bucketMetricCfg, alarmNames):
    bucketName = bucketMetricCfg["BucketName"]
    metricCfgId = bucketMetricCfg["Id"]
    alarmName = f'AWS/S3-5xxRate-{bucketName}-{metricCfgId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(bucketMetricCfg.get('TagList', []), '5xxRate', 1)
    
    alarm_actions, ok_actions = common.getSSMActions(account_id, region, bucketMetricCfg.get('TagList', []))
    client = boto3.client('cloudwatch', region_name=region)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'S3桶{bucketName}, 统计范围{metricCfgId}, 5xx错误率超过阈值{threshold}',
        ActionsEnabled=True,
        AlarmActions=alarm_actions,
        OKActions=ok_actions,
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
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True
    
def createOperationsFailedReplicationAlarm(region, bucketReliationRule, alarmNames):
    sourceBucketName = bucketReliationRule["SourceBucketName"]
    ruleId = bucketReliationRule["ID"]
    destinationBucketName = bucketReliationRule["Destination"]["Bucket"]
    alarmName = f'AWS/S3-OperationsFailedReplication-{sourceBucketName}-{destinationBucketName}-{ruleId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False

    alarm_actions, ok_actions = common.getSSMActions(account_id, region, bucketReliationRule.get('TagList', []))
    client = boto3.client('cloudwatch', region_name=region)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'S3桶{sourceBucketName}复制到{destinationBucketName}出现失败，规则ID: {ruleId}',
        ActionsEnabled=True,
        AlarmActions=alarm_actions,
        OKActions=ok_actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/S3',
                        'MetricName': '5xxErrors',
                        'Dimensions': [
                            {
                                'Name': 'SourceBucket',
                                'Value': sourceBucketName
                            },
                            {
                                'Name': 'DestinationBucket',
                                'Value': destinationBucketName
                            },
                            {
                                'Name': 'RuleId',
                                'Value': ruleId
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'Label': ruleId,
                'ReturnData': True,
            }
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=0,
        ComparisonOperator='GreaterThanThreshold',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    numOfAlarmsCreated = 0
    alarmsDeleted = []
    for r in os.getenv('TargetRegions', os.getenv('AWS_REGION')).split(','):
        region = r.strip()
        logger.info(f'Remediating S3 alarms in region {region}')
        # 获取当前区域所有S3桶
        client = boto3.client('s3')
        response = client.list_buckets()
        bucketList = []
        for bucket in response["Buckets"]:
            response = client.get_bucket_location(Bucket=bucket['Name'])
            bucketLocation = response.get('LocationConstraint') if response.get('LocationConstraint') else 'us-east-1'
            if bucketLocation == region:
                bucketList.append(bucket)
                
        # 获取已创建的告警
        client = boto3.client('cloudwatch', region_name=region)
        paginator = client.get_paginator('describe_alarms')
        page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/S3-')
        alarmNames = []
        for page in page_iterator:
            alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))
    
        # 创建告警
        for bucket in bucketList:
            client = boto3.client('s3', region_name=region)
            #获取标签
            try:
                response = client.get_bucket_tagging(Bucket=bucket['Name'])
                bucket['TagSet'] = response.get('TagSet', [])
            except:
                bucket['TagSet'] = []
            #请求指标
            response = client.list_bucket_metrics_configurations(Bucket=bucket['Name'])
            metriCfgList = response.get('MetricsConfigurationList', [])
            for metricCfg in metriCfgList:
                metricCfg['BucketName'] = bucket['Name']
                metricCfg['TagList'] = bucket['TagSet']
                alarmName, created = create5xxRateAlarm(region, metricCfg, alarmNames)
                numOfAlarmsCreated += 1 if created else 0
            #复制指标
            replicationRules = []
            try:
                response = client.get_bucket_replication(Bucket=bucket['Name'])
                replicationRules = response["ReplicationConfiguration"]["Rules"]
            except:
                pass
            for rule in replicationRules:
                rule['SourceBucketName'] = bucket['Name']
                rule['TagList'] = bucket['TagSet']
                alarmName, created = createOperationsFailedReplicationAlarm(region, rule, alarmNames)
                numOfAlarmsCreated += 1 if created else 0   
    
    
        # 删除不再使用的告警
        logger.info(f'Delete orphan alarms: {alarmNames}')
        client = boto3.client('cloudwatch')
        for x in range(0, len(alarmNames), 100):
            response = client.delete_alarms(
                AlarmNames=alarmNames[x:x+100]
            )
        alarmsDeleted += map(lambda x: f'{region}:{x}', alarmNames)

    event["numOfAlarmsCreated"] = event.get("numOfAlarmsCreated", 0) + numOfAlarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmsDeleted
    logger.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})


