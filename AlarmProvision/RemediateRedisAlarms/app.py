import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

def createCPUUtilizationAlarm(node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-CPUUtilization-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='CPU利用率',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [
                            {
                                'Name': 'CacheClusterId',
                                'Value': nodeId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': nodeId,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=80,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createCPUCreditBalanceAlarm(node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-CPUCreditBalance-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='CPU积分余额',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'CPUCreditBalance',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': nodeId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': nodeId,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=60,
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createInstanceNetworkBandwidthlarm(node, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-NetworkBandwidth-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    baselineBandwidthInGbps = instanceTypes[node["CacheNodeType"].strip("cache.")]["NetworkInfo"]["NetworkCards"][0].get("BaselineBandwidthInGbps")
    maxBandwidthInGbps = instanceTypes[node["CacheNodeType"].strip("cache.")]["NetworkInfo"]["NetworkCards"][0].get("PeakBandwidthInGbps")
    if not baselineBandwidthInGbps:
        return alarmName, False
    base_throughput=baselineBandwidthInGbps*1000*1000*1000/8
    max_throughput=maxBandwidthInGbps*1000*1000*1000/8
    threshold = 0.8*max_throughput if max_throughput==base_throughput else base_throughput
    logging.info(f'Network Base Throughput: ${base_throughput}, Max Throughput: {max_throughput}, Threshold: {threshold}')
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='实例网络带宽限制。参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/instance-types.html#instance-type-summary-table。对于不可突增实例（基线性能等于最大性能），告警阈值为限制的的80%，对于可突增实例（基准性能低于最大性能, 通常，有 16 个或更少 vCPU 的实例（大小为 4xlarge 或更小）被记录为具有“高达”的指定带宽；例如，“高达 10 Gbps”。这些实例具备基准带宽。为满足其他需求，可以使用网络 I/O 积分机制，以突增超出其基准带宽。实例可以在有限时间内使用突增带宽，通常为5到60分钟，具体取决于实例的大小。），告警阈值为基线性能',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'NetworkBytesIn',
                        'Dimensions': [
                            {
                                'Name': 'CacheClusterId',
                                'Value': nodeId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': nodeId,
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'NetworkBytesOut',
                        'Dimensions': [
                            {
                                'Name': 'CacheClusterId',
                                'Value': nodeId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': nodeId,
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'MAX([m1,m2])/PERIOD(m1)',
                'Label': nodeId,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=threshold,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True
    
def getInstanceTypes(): 
    # 获取所有EC2实例类型
    client = boto3.client('ec2')
    paginator = client.get_paginator('describe_instance_types')
    page_iterator = paginator.paginate()
    result = {}
    for page in page_iterator:
        for r in page["InstanceTypes"]:
            result[r["InstanceType"]] = r
    return result

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    instanceTypeMap = getInstanceTypes()
    # 获取所有Cache实例
    client = boto3.client('elasticache')
    paginator = client.get_paginator('describe_cache_clusters')
    page_iterator = paginator.paginate()
    cacheNodeList = []
    for page in page_iterator:
        for cache in page["CacheClusters"]:
            if cache["Engine"]=='redis':
                cacheNodeList.append(cache)
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    paginator = client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/ElastiCache-')
    alarmNames = []
    for page in page_iterator:
        alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))

    # 创建告警
    numOfAlarmsCreated = 0
    for node in cacheNodeList:
        alarmName, created = createCPUUtilizationAlarm(node, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
        if node["CacheNodeType"].startswith('cache.t'):
            alarmName, created = createCPUCreditBalanceAlarm(node, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
        alarmName, created = createInstanceNetworkBandwidthlarm(node, instanceTypeMap, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
            
    # 删除不再使用的告警
    logging.info(f'Delete orphan alarms: {alarmNames}')
    for x in range(0, len(alarmNames), 100):
        response = client.delete_alarms(
            AlarmNames=alarmNames[x:x+100]
        )

    event["numOfAlarmsCreated"] = event.get("numOfAlarmsCreated", 0) + numOfAlarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmNames
    logging.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})


