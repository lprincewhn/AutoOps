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

def createCPUUtilizationAlarm(region, node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-CPUUtilization-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(node.get("TagList"), "CPUUtilization", 80)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Redis实例{nodeId}CPU利用率超出阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
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
        Threshold=threshold,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createEngineCPUUtilizationAlarm(region, node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-EngineCPUUtilization-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(node.get("TagList"), "EngineCPUUtilization", 80)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Redis实例{nodeId} Redis引擎线程所在CPU利用率超出阈值{threshold}。由于Redis是单线程的，您可以使用该指标来分析Redis进程本身的负载。EngineCPUUtilization 指标更精确地呈现了 Redis 流程。您可以将其与 CPUUtilization 指标配合使用。CPUUtilization 公开服务器实例整体的 CPU 使用率，包括其他操作系统和管理流程。对于有四个或更多 vCPU 的较大节点类型，可使用 EngineCPUUtilization 指标来监控和设置扩展阈值。注意：在 ElastiCache 主机上，后台进程将监控主机以提供托管式数据库体验。这些后台进程可能会占用很大一部分 CPU 工作负载。这在具有两个以上 vCPU 的大型主机上影响不大，但在 vCPU 个数不超过 2 个的小型主机上影响较大。如果仅监控 EngineCPUUtilization 指标，您将无法发现因 Redis 或后台监控进程的 CPU 使用率过高而导致主机过载情况。因此，我们建议对于具有不超过两个 vCPU 的主机，还需要监控 CPUUtilization 指标',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'EngineCPUUtilization',
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
        Threshold=threshold,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createCPUCreditBalanceAlarm(region, node, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-CPUCreditBalance-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    vcpus = instanceTypes[node["CacheNodeType"].strip('cache.')]["VCpuInfo"]["DefaultVCpus"]
    if not vcpus:
        return alarmName, False
    threshold = vcpus*common.getThreshold(node.get("TagList"), "CreditSupportMinute", 30)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Redis实例{nodeId}CPU积分低于阈值{threshold} (1个CPU积分=1个vCPU*100%利用率*1分钟)。请参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html#key-concepts',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'CPUCreditBalance',
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
        Threshold=threshold,
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createDatabaseMemoryUsagePercentageAlarm(region, node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-DatabaseMemoryUsagePercentage-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(node.get("TagList"), "DatabaseMemoryUsagePercentage", 80)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Redis实例{nodeId}内存使用率大于阈值{threshold}。这是使用used_memory/maxmemory从Redis INFO命令计算得来，maxmemory已经排除通过reserved-memory参数预留出来的内存',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'DatabaseMemoryUsagePercentage',
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
        Threshold=threshold,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createSwapUsageAlarm(region, node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-SwapUsage-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(node.get("TagList"), "SwapUsageMB", 50)*1024*1024
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Redis实例{nodeId}Swap空间使用量超出阈值{threshold}, 开始使用SWAP空间通常表示内存不足',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'SwapUsage',
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
        Threshold=threshold,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True
    
def createInstanceNetworkBandwidthlarm(region, node, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
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
    threshold = common.getThreshold(node.get("TagList"), "MaxNetworkBandwidth", 0.8)*max_throughput if max_throughput==base_throughput else common.getThreshold(node.get("TagList"), "BaseNetworkBandwidth", 1)*base_throughput
    logger.info(f'Network Base Throughput: {base_throughput}, Max Throughput: {max_throughput}, Threshold: {threshold}')
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Redis实例{nodeId}网络带宽超出阈值{threshold} Bytes/sec。参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/instance-types.html#instance-type-summary-table。对于不可突增实例（基线性能等于最大性能），告警阈值为限制的的80%，对于可突增实例（基准性能低于最大性能, 通常，有 16 个或更少 vCPU 的实例（大小为 4xlarge 或更小）被记录为具有“高达”的指定带宽；例如，“高达 10 Gbps”。这些实例具备基准带宽。为满足其他需求，可以使用网络 I/O 积分机制，以突增超出其基准带宽。实例可以在有限时间内使用突增带宽，通常为5到60分钟，具体取决于实例的大小。），告警阈值为基线性能',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
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
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createInstanceNetworkAllowanceExceededlarm(region, node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-NetworkAllowanceExceeded-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Redis实例{nodeId}网络超限，出现丢包。参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/monitoring-network-performance-ena.html',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'NetworkBandwidthInAllowanceExceeded',
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
                'Label': 'NetworkBandwidthInAllowanceExceeded',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'NetworkBandwidthOutAllowanceExceeded',
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
                'Label': 'NetworkBandwidthOutAllowanceExceeded',
                'ReturnData': False,
            },
            {
                'Id': 'm3',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'NetworkConntrackAllowanceExceeded',
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
                'Label': 'NetworkConntrackAllowanceExceeded',
                'ReturnData': False,
            },
            {
                'Id': 'm4',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'NetworkPacketsPerSecondAllowanceExceeded',
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
                'Label': 'NetworkPacketsPerSecondAllowanceExceeded',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1+m2+m3+m4',
                'Label': nodeId,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=0,
        ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True
    
def createCurrConnectionsAlarm(region, node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    nodeId = node["CacheClusterId"]
    alarmName = f'AWS/ElastiCache-CurrConnections-{nodeId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(node.get("TagList"), "CurrConnections", 60000)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Redis实例{nodeId}并发连接数超出阈值{threshold}，每个Redis节点有65000并发连接上限的硬限制',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ElastiCache',
                        'MetricName': 'CurrConnections',
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
        Threshold=threshold,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    instanceTypeMap = common.getInstanceTypes()
    numOfAlarmsCreated = 0
    alarmsDeleted = []
    for r in os.getenv('TargetRegions', os.getenv('AWS_REGION')).split(','):
        region = r.strip()
        logger.info(f'Remediating Redis alarms in region {region}')
        # 获取所有Cache实例
        client = boto3.client('elasticache', region_name=region)
        paginator = client.get_paginator('describe_cache_clusters')
        page_iterator = paginator.paginate()
        cacheNodeList = []
        for page in page_iterator:
            for cache in page["CacheClusters"]:
                if cache["Engine"]=='redis':
                    response = client.list_tags_for_resource(ResourceName=cache["ARN"])
                    cache["TagList"] = response["TagList"]
                    cacheNodeList.append(cache)
        # 获取已创建的告警
        client = boto3.client('cloudwatch', region_name=region)
        paginator = client.get_paginator('describe_alarms')
        page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/ElastiCache-')
        alarmNames = []
        for page in page_iterator:
            alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))
        # 创建告警
        for node in cacheNodeList:
            alarmName, created = createCPUUtilizationAlarm(region, node, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
            if node["CacheNodeType"].startswith('cache.t'):
                alarmName, created = createCPUCreditBalanceAlarm(region, node, instanceTypeMap, alarmNames)
                numOfAlarmsCreated += 1 if created else 0 
            alarmName, created = createEngineCPUUtilizationAlarm(region, node, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
            alarmName, created = createDatabaseMemoryUsagePercentageAlarm(region, node, alarmNames)
            numOfAlarmsCreated += 1 if created else 0    
            alarmName, created = createSwapUsageAlarm(region, node, alarmNames)
            numOfAlarmsCreated += 1 if created else 0    
            alarmName, created = createInstanceNetworkBandwidthlarm(region, node, instanceTypeMap, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createInstanceNetworkAllowanceExceededlarm(region, node, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createCurrConnectionsAlarm(region, node, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
                
        # 删除不再使用的告警
        logger.info(f'Delete orphan alarms: {alarmNames}')
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


