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
    clusterName = node["ClusterName"]
    brokerId = str(node["BrokerNodeInfo"]["BrokerId"])
    alarmName = f'AWS/Kafka-CPUUtilization-{clusterName}-{brokerId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(node.get('TagList', []), 'CPUUtilization', 60)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Kafka集群{clusterName}代理节点{brokerId} CPU利用率超过阈值{threshold}。Amazon MSK 强烈建议您将代理的总 CPU 使用率（定义为 CPU User + CPU System）保持在 60% 以下。当集群的总 CPU 可用率至少达到 40% 时，Apache Kafka 可以在必要时在集群中的代理之间重新分配 CPU 负载。例如，当 Amazon MSK 检测到代理故障并从中恢复时，就有必要这样做；在这种情况下，Amazon MSK 会执行自动维护，如进行修补。另一个例子是当用户请求更改代理类型或升级版本时；在这两种情况下，Amazon MSK 会部署滚动工作流程，一次让一个代理离线。当具有领导分区的代理离线时，Apache Kafka 会重新分配分区领导权，以将工作重新分配给集群中的其他代理。通过遵循此最佳实践，您可以确保集群中有足够的 CPU 余量来容忍此类操作事件',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'CpuSystem',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': 'CpuSystem',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'CpuUser',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': 'Kafka',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1+m2',
                'Label': f'{clusterName}-{brokerId}',
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

def createCPUCreditBalanceAlarm(region, node, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clusterName = node["ClusterName"]
    brokerId = str(node["BrokerNodeInfo"]["BrokerId"])
    alarmName = f'AWS/Kafka-CPUCreditBalance-{clusterName}-{brokerId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    vcpus = instanceTypes[node["InstanceType"]]["VCpuInfo"]["DefaultVCpus"]
    threshold = vcpus*common.getThreshold(node.get('Tags', []), 'CreditSupportMinute', 30)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Kafka集群{clusterName}代理节点{brokerId} CPU积分低于阈值{threshold} (1个CPU积分=1个vCPU*100%利用率*1分钟)。请参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html#key-concepts',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'CPUCreditBalance',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': f'{clusterName}-{brokerId}',
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=threshold,
        ComparisonOperator='LessThanThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createKafkaDataLogsDiskUsedAlarm(region, node, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clusterName = node["ClusterName"]
    brokerId = str(node["BrokerNodeInfo"]["BrokerId"])
    alarmName = f'AWS/Kafka-KafkaDataLogsDiskUsed-{clusterName}-{brokerId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(node.get('Tags', []), 'KafkaDataLogsDiskUsed', 85)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Kafka集群{clusterName}代理节点{brokerId} 存储空间使用率{threshold}。要避免出现因磁盘空间不足而无法保存消息的情况，您可以创建一个 CloudWatch 警报器监视KafkaDataLogsDiskUsed指标。当此指标的值达到或超过 85% 时，请执行下列一项或多项操作：1.使用自动扩展。您也可以手动增加代理存储空间，如中所述手动扩展; 2.缩短消息保留期或减小日志大小。有关如何做到这一点的信息，请参阅调整数据保留参数; 3.删除未使用的主题',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'KafkaDataLogsDiskUsed',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': f'{clusterName}-{brokerId}',
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
    
def createHeapMemoryAfterGCAlarm(region, node, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clusterName = node["ClusterName"]
    brokerId = str(node["BrokerNodeInfo"]["BrokerId"])
    alarmName = f'AWS/Kafka-HeapMemoryAfterGC-{clusterName}-{brokerId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(node.get('Tags', []), 'HeapMemoryAfterGC', 60)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Kafka集群{clusterName}代理节点{brokerId} 内存堆使用率{threshold}。HeapMemoryAfterGC是垃圾回收后使用中的总堆内存的百分比。建议您创建一个 CloudWatch 警报在以下情况下采取行动HeapMemoryAfterGC增加到 60% 以上。您可以执行的减少内存使用率的步骤各不相同。它们取决于你配置 Apache Kafka 的方式。例如，如果您使用事务性消息传递，则可以减少transactional.id.expiration.ms你的 Apache Kafka 配置中的值来自604800000ms 到86400000毫秒（从 7 天到 1 天）。这减少了每个事务的内存占用',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'HeapMemoryAfterGC',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': f'{clusterName}-{brokerId}',
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
     
def createIopsAlarm(region, node, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clusterName = node["ClusterName"]
    brokerId = str(node["BrokerNodeInfo"]["BrokerId"])
    alarmName = f'AWS/Kafka-IOPS-{clusterName}-{brokerId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    
    #实例侧限制
    instance_base_iops =  instance_max_iops = instance_threshold = 0   
    ebsOptimizedInfo = instanceTypes[node["InstanceType"]]["EbsInfo"].get("EbsOptimizedInfo")
    if ebsOptimizedInfo:
        instance_base_iops=ebsOptimizedInfo["BaselineIops"]
        instance_max_iops=ebsOptimizedInfo["MaximumIops"]
        instance_threshold = common.getThreshold(node.get('Tags', []), 'MaxIOPS', 0.8)*instance_max_iops if instance_max_iops==instance_base_iops else common.getThreshold(node.get('Tags', []), 'BaseIOPS', 1)*instance_base_iops
        logger.info(f'Instance Base IOPS: {instance_base_iops}, Max IOPS: {instance_max_iops}, Threshold={instance_threshold}')   

    #存储侧限制，MSK仅支持gp2存储
    # 在最小 100 IOPS（33.33GiB 及以下）和最大 16,000 IOPS（5334GiB 及以上）之间，基准性能以每 GiB 卷大小 3 IOPS 的速度线性扩展。
    ebs_base_iops = max(min(node["StorageInfo"]["EbsStorageInfo"]["VolumeSize"]*3, 16000), 100)
    ebs_max_iops = max(3000, ebs_base_iops)
    ebs_threshold = common.getThreshold(node.get('Tags', []), 'MaxIOPS', 0.8)*ebs_max_iops if ebs_max_iops==ebs_base_iops else common.getThreshold(node.get('Tags', []), 'BaseIOPS', 1)*ebs_base_iops
    logger.info(f'EBS Base IOPS: {ebs_base_iops}, Max IOPS: {ebs_max_iops}, Threshold: {ebs_threshold}')  

    threshold = min(instance_threshold, ebs_threshold)   
    if threshold==0:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Kafka集群{clusterName}代理节点{brokerId} IOPS超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'VolumeWriteOps',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'VolumeWriteOps',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'VolumeReadOps',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'VolumeReadOps',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': '(m1+m2)/PERIOD(m1)',
                'Label': f'{clusterName}-{brokerId}',
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

def createThroughputAlarm(region, node, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clusterName = node["ClusterName"]
    brokerId = str(node["BrokerNodeInfo"]["BrokerId"])
    alarmName = f'AWS/Kafka-Thrughput-{clusterName}-{brokerId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    
    #实例侧限制
    instance_base_throughput =  instance_max_throughput = instance_threshold = 0   
    ebsOptimizedInfo = instanceTypes[node["InstanceType"]]["EbsInfo"].get("EbsOptimizedInfo")
    if ebsOptimizedInfo:
        instance_base_throughput=ebsOptimizedInfo["BaselineBandwidthInMbps"]*1000*1000/8
        instance_max_throughput=ebsOptimizedInfo["MaximumBandwidthInMbps"]*1000*1000/8
        instance_threshold = common.getThreshold(node.get('Tags', []), 'MaxThroughput', 0.8)*instance_max_throughput if instance_max_throughput==instance_base_throughput else common.getThreshold(node.get('Tags', []), 'BaseThroughput', 1)*instance_base_throughput
        logger.info(f'Instance Base Throughput: {instance_base_throughput}, Max Throughput: {instance_max_throughput}, Threshold={instance_threshold}')   

    #存储侧限制，MSK仅支持gp2存储
    ebs_base_throughput = ebs_max_throughput = ebs_threshold = 100000*1024*1024
    # 吞吐量限制介于 128 MiB/s 和 250 MiB/s 之间，具体取决于卷大小。小于或等于 170 GiB 的卷提供最大 128 MiB/s 的吞吐量。如果有突增积分可用，大于 170 GiB 但小于 334 GiB 的卷将提供 250 的最大吞吐量。无论突增点数是多少，大于或等于 334 GiB 的卷均可提供 250 MiB/s。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/general-purpose.html
    if node["StorageInfo"]["EbsStorageInfo"]["VolumeSize"] >= 334:
        ebs_base_throughput = ebs_max_throughput = 250*1024*1024
    elif node["StorageInfo"]["EbsStorageInfo"]["VolumeSize"] >= 170:
        ebs_max_throughput = 250*1024*1024       
        ebs_base_throughput = 0.2 * ebs_max_throughput
    else:
        ebs_max_throughput = 128*1024*1024
        ebs_base_throughput = 0.2 * ebs_max_throughput
    ebs_threshold = common.getThreshold(node.get('Tags', []), 'MaxThroughtput', 0.8)*ebs_max_throughput if ebs_max_throughput==ebs_base_throughput else common.getThreshold(node.get('Tags', []), 'BaseThroughput', 1)*ebs_base_throughput
    logger.info(f'EBS Base IOPS: {ebs_base_throughput}, Max IOPS: {ebs_max_throughput}, Threshold: {ebs_threshold}')  

    threshold = min(instance_threshold, ebs_threshold)   
    if threshold==0:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Kafka集群{clusterName}代理节点{brokerId} IOPS超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'VolumeWriteBytes',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'VolumeWriteBytes',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'VolumeReadBytes',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'VolumeReadBytes',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': '(m1+m2)/PERIOD(m1)',
                'Label': f'{clusterName}-{brokerId}',
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

def createInstanceNetworkAllowanceExceededlarm(region, node, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clusterName = node["ClusterName"]
    brokerId = str(node["BrokerNodeInfo"]["BrokerId"])
    alarmName = f'AWS/Kafka-NetworkAllowanceExceeded-{clusterName}-{brokerId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False

    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'Kafka集群{clusterName}代理节点{brokerId}网络超限，出现丢包。参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/monitoring-network-performance-ena.html',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'BwInAllowanceExceeded',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'BwInAllowanceExceeded',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'BwOutAllowanceExceeded',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'BwOutAllowanceExceeded',
                'ReturnData': False,
            },
            {
                'Id': 'm3',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'ConnTrackAllowanceExceeded',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'ConnTrackAllowanceExceeded',
                'ReturnData': False,
            },
            {
                'Id': 'm4',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/Kafka',
                        'MetricName': 'PpsAllowanceExceeded',
                        'Dimensions': [
                            {
                                'Name': 'Cluster Name',
                                'Value': clusterName
                            },
                            {
                                'Name': 'Broker ID',
                                'Value': brokerId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'PpsAllowanceExceeded',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1+m2+m3+m4',
                'Label': f'{clusterName}-{brokerId}',
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
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    instanceTypeMap = common.getInstanceTypes()
    numOfAlarmsCreated = 0
    alarmsDeleted = []
    for r in os.getenv('TargetRegions', os.getenv('AWS_REGION')).split(','):
        region = r.strip()
        logger.info(f'Remediating Kafka alarms in region {region}')
        # 获取所有Kafka集群
        client = boto3.client('kafka', region_name=region)
        paginator = client.get_paginator('list_clusters')
        page_iterator = paginator.paginate()
        kafkaClusterList = []
        for page in page_iterator:
            for cluster in page["ClusterInfoList"]:
                kafkaClusterList.append(cluster)
        # 获取已创建的告警
        client = boto3.client('cloudwatch', region_name=region)
        paginator = client.get_paginator('describe_alarms')
        page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/Kafka-')
        alarmNames = []
        for page in page_iterator:
            alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))
    
        # 创建告警
        for cluster in kafkaClusterList:
            client = boto3.client('kafka', region_name=region)
            response = client.list_nodes(ClusterArn=cluster['ClusterArn'])
            nodeList = response['NodeInfoList']
            for node in nodeList:
                node["ClusterName"] = cluster["ClusterName"]
                node["StorageInfo"] = cluster["BrokerNodeGroupInfo"]["StorageInfo"]
                node["Tags"] = cluster["Tags"]
                alarmName, created = createCPUUtilizationAlarm(region, node, alarmNames)
                numOfAlarmsCreated += 1 if created else 0
                alarmName, created = createKafkaDataLogsDiskUsedAlarm(region, node, instanceTypeMap, alarmNames)  
                numOfAlarmsCreated += 1 if created else 0
                alarmName, created = createHeapMemoryAfterGCAlarm(region, node, instanceTypeMap, alarmNames) 
                numOfAlarmsCreated += 1 if created else 0
                if node["InstanceType"].startswith('t'):
                    alarmName, created = createCPUCreditBalanceAlarm(region, node, instanceTypeMap, alarmNames) 
                    numOfAlarmsCreated += 1 if created else 0
                if cluster["EnhancedMonitoring"] in ["PER_BROKER", "PER_TOPIC_PER_BROKER", "PER_TOPIC_PER_PARTITION"]:
                    alarmName, created = createIopsAlarm(region, node, instanceTypeMap, alarmNames)   
                    numOfAlarmsCreated += 1 if created else 0
                    alarmName, created = createThroughputAlarm(region, node, instanceTypeMap, alarmNames)   
                    numOfAlarmsCreated += 1 if created else 0
                    alarmName, created = createInstanceNetworkAllowanceExceededlarm(region, node, alarmNames) 
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


