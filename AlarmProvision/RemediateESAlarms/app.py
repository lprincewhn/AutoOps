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


def createRedClusterAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-ClusterStatus.red-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName}变为红色，表示至少有一个主分片其及副本未分配给节点',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ClusterStatus.red',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': domainName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=0,
        ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createYellowClusterAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-ClusterStatus.yellow-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName}变为黄色，至少有一个副本分片未分配给节点',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ClusterStatus.yellow',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': domainName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=5,
        DatapointsToAlarm=5,
        Threshold=0,
        ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createClusterIndexWritesBlockedAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-ClusterIndexWritesBlocked-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName}阻止传入的写入请求。一些常见的因素包括：FreeStorageSpace 过低或 JVMMemoryPressure 过高。为了缓解这一问题，可以考虑增加磁盘空间或扩展集群',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ClusterIndexWritesBlocked',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': domainName,
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
    
def createFreeStorageSpaceAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-FreeStorageSpace-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(domain.get('TagList', []), 'FreeStorageSpace', 20)*1024
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'ElastiSearch集群{domainName}存储剩余空间最少的数据节点值低于阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'FreeStorageSpace',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Minimum',
                },
                'Label': domainName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=threshold,
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True    

def createNodesAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-Nodes-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold=domain['ElasticsearchClusterConfig']['InstanceCount']
    if domain['ElasticsearchClusterConfig']['DedicatedMasterEnabled']:
        threshold+=domain['ElasticsearchClusterConfig'].get('DedicatedMasterCount', 0)
    if domain['ElasticsearchClusterConfig']['WarmEnabled']:
        threshold+=domain['ElasticsearchClusterConfig'].get('WarmCount', 0)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName}中的健康节点数量(包括专用主节点和UltraWarm节点)低于配置数量。此警报表示您的群集中至少有一个节点无法访问的时间已达到一天',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'Nodes',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 86400,
                    'Stat': 'Minimum',
                },
                'Label': domainName,
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
   
def createAutomatedSnapshotFailureAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-AutomatedSnapshotFailure-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName}自动快照失败。此故障通常由红色群集运行状况导致',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'AutomatedSnapshotFailure',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Minimum',
                },
                'Label': domainName,
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
      
def createCPUUtilizationAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-CPUUtilization-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(domain.get('TagList', []), 'CPUUtilization', 80)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName} CPU利用率最大的数据节点值超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Maximum',
                },
                'Label': domainName,
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

def createCPUCreditBalanceAlarm(region, domain, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-CPUCreditBalance-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    vcpus = instanceTypes[domain["ElasticsearchClusterConfig"]["InstanceType"][:-14]]["VCpuInfo"]["DefaultVCpus"]
    threshold = vcpus*common.getThreshold(domain.get('TagList', []), 'CreditSupportMinute', 30)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName} CPU积分最少的数据节点值低于阈值{threshold} (1个CPU积分=1个vCPU*100%利用率*1分钟)。请参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html#key-concepts',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'CPUCreditBalance',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Minimum',
                },
                'Label': domainName,
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
    
def createJVMMemoryPressureAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-JVMMemoryPressure-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(domain.get('TagList', []), 'JVMMemoryPressure', 95)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'ElastiSearch集群{domainName}Java堆利用率最大的数据节点值超过阈值{threshold}。OpenSearch服务将实例内存的一半用于Java堆，堆大小不超过32GiB',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'JVMMemoryPressure',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Maximum',
                },
                'Label': domainName,
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

def createKMSKeyErrorAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-KMSKeyError-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName}用于加密静态数据的 AWS KMS 加密密钥已禁用。重新启用它可恢复正常操作。',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'KMSKeyError',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': domainName,
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

def createKMSKeyInaccessibleAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-KMSKeyInaccessible-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName}用于AWS KMS加密您域中静态数据的加密密钥已被删除或已撤销其对 Serv OpenSearch ice 的授权。您无法恢复处于此状态的域。但如果您具有手动快照，则可以使用它迁移到新域',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'KMSKeyInaccessible',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': domainName,
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
     
def createIopsAlarm(region, domain, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-IOPS-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    
    #实例侧限制
    instance_base_iops =  instance_max_iops = instance_threshold = 0   
    ebsOptimizedInfo = instanceTypes[domain["ElasticsearchClusterConfig"]["InstanceType"][:-14]]["EbsInfo"].get("EbsOptimizedInfo")
    if ebsOptimizedInfo:
        instance_base_iops=ebsOptimizedInfo["BaselineIops"]
        instance_max_iops=ebsOptimizedInfo["MaximumIops"]
        instance_threshold = common.getThreshold(domain.get('TagList', []), 'MaxIOPS', 0.8)*instance_max_iops if instance_max_iops==instance_base_iops else common.getThreshold(domain.get('TagList', []), 'BaseIOPS', 1)*instance_base_iops
        logger.info(f'Instance Base IOPS: {instance_base_iops}, Max IOPS: {instance_max_iops}, Threshold={instance_threshold}')   

    #存储侧限制, Aurora和DocumentDB无此限制
    ebs_base_iops = ebs_max_iops = ebs_threshold = 10000000000000
    if domain["EBSOptions"]['VolumeType'] == 'gp2':
        # 在最小 100 IOPS（33.33GiB 及以下）和最大 16,000 IOPS（5334GiB 及以上）之间，基准性能以每 GiB 卷大小 3 IOPS 的速度线性扩展。
        ebs_base_iops = max(min(domain["EBSOptions"]["VolumeSize"]*3, 16000), 100)
        ebs_max_iops = max(3000, ebs_base_iops)
    elif domain["EBSOptions"]['VolumeType'] == 'io1':
        ebs_base_iops = ebs_max_iops = domain["EBSOptions"]["Iops"]
    elif domain["EBSOptions"]['VolumeType'] == 'gp3':
        ebs_base_iops = ebs_max_iops = max(domain["EBSOptions"]["Iops"], 3000)
    ebs_threshold = common.getThreshold(domain.get('TagList', []), 'MaxIOPS', 0.8)*ebs_max_iops if ebs_max_iops==ebs_base_iops else common.getThreshold(domain.get('TagList', []), 'BaseIOPS', 1)*ebs_base_iops
    logger.info(f'EBS Base IOPS: {ebs_base_iops}, Max IOPS: {ebs_max_iops}, Threshold: {ebs_threshold}')  

    threshold = min(instance_threshold, ebs_threshold)   
    if threshold==0:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName} IOPS最大的数据节点值超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ReadIOPS',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Maximum',
                },
                'Label': 'ReadIOPS',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'WriteIOPS',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Maximum',
                },
                'Label': 'WriteIOPS',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1+m2',
                'Label': domainName,
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

def createThroughputAlarm(region, domain, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-Throughput-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    
    #实例侧限制
    instance_base_throughput =  instance_max_throughput = instance_threshold = 0   
    ebsOptimizedInfo = instanceTypes[domain["ElasticsearchClusterConfig"]["InstanceType"][:-14]]["EbsInfo"].get("EbsOptimizedInfo")
    if ebsOptimizedInfo:
        instance_base_throughput=ebsOptimizedInfo["BaselineBandwidthInMbps"]*1000*1000/8
        instance_max_throughput=ebsOptimizedInfo["MaximumBandwidthInMbps"]*1000*1000/8
        instance_threshold = common.getThreshold(domain.get('TagList', []), 'MaxThroughput', 0.8)*instance_max_throughput if instance_max_throughput==instance_base_throughput else common.getThreshold(domain.get('TagList', []), 'BaseThroughput', 1)*instance_base_throughput
        logger.info(f'Instance Base Throughput: {instance_base_throughput}, Max Throughput: {instance_max_throughput}, Threshold={instance_threshold}')   

    ebs_base_throughput = ebs_max_throughput = ebs_threshold = 100000*1024*1024
    if domain["EBSOptions"]['VolumeType'] == 'gp2':
        # 吞吐量限制介于 128 MiB/s 和 250 MiB/s 之间，具体取决于卷大小。小于或等于 170 GiB 的卷提供最大 128 MiB/s 的吞吐量。如果有突增积分可用，大于 170 GiB 但小于 334 GiB 的卷将提供 250 的最大吞吐量。无论突增点数是多少，大于或等于 334 GiB 的卷均可提供 250 MiB/s。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/general-purpose.html
        if domain["EBSOptions"]["VolumeSize"] >= 334:
            ebs_base_throughput = ebs_max_throughput = 250*1024*1024
        elif domain["EBSOptions"]["VolumeSize"] >= 170:
            ebs_max_throughput = 250*1024*1024       
            ebs_base_throughput = 0.2 * ebs_max_throughput
        else:
            ebs_max_throughput = 128*1024*1024
            ebs_base_throughput = 0.2 * ebs_max_throughput
    elif domain["EBSOptions"]['VolumeType'] == 'io1':
        # 预置了最高 32000 IOPS 的 Provisioned IOPS SSD 卷支持 256 KiB 的最大 I/O 大小，可以达到最高 500 MiB/s 的吞吐量。当 I/O 大小达到最大时，吞吐量也将达到峰值 2000 IOPS。预置超过 32,000 IOPS（最高可达 64,000 IOPS）的卷以每预置 IOPS 16 KiB 的速率线性增加吞吐量。例如，预置了 48,000 IOPS 的卷可以支持高达 750 MiB/s 的吞吐量（每个预置 IOPS 16 KiB x 48,000 个预置 IOPS = 750 Mib/s）。要实现 1,000 MiB/s 的最大吞吐量，必须为卷预置 64,000 IOPS（每个预置 IOPS 16 KiB x 64,000 个预置 IOPS = 1,000 Mib/s）。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/provisioned-iops.html
        ebs_max_throughput = ebs_base_throughput = max(domain["Iops"]*16*1024, 1000*1024*1024)
    elif domain["EBSOptions"]['VolumeType'] == 'gp3':
        ebs_max_throughput = ebs_base_throughput = max(domain.get("Throughput", 0)*1024*1024, 125*1024*1024) 
    ebs_threshold = common.getThreshold(domain.get('TagList', []), 'MaxThroughput', 0.8)*ebs_max_throughput if ebs_max_throughput==ebs_base_throughput else common.getThreshold(domain.get('TagList', []), 'BaseThroughput', 1)*ebs_base_throughput
    logger.info(f'EBS Base Throughput: {ebs_base_throughput}, Max Throughput: {ebs_max_throughput}, Threshold={ebs_threshold}') 
    
    threshold = min(instance_threshold, ebs_threshold)   
    if threshold==0:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName} IO吞吐量最大的数据节点值超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ReadThroughput',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Maximum',
                },
                'Label': 'ReadThroughput',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'WriteThroughput',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Maximum',
                },
                'Label': 'WriteThroughput',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1+m2',
                'Label': domainName,
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

def createActiveShardsAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-ActiveShards-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(domain.get('TagList', []), 'ActiveShards', 30000)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'ElastiSearch集群{domainName}活动主分区和副本分区的总数大于{threshold}。轮换索引的频率可能过于频繁。请考虑使用 ISM 在索引达到特定使用期限之后将其移除。',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'Shards.active',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Maximum',
                },
                'Label': domainName,
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

def createMasterReachableFromNodeAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-MasterReachableFromNode-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'ElastiSearch集群{domainName}主节点已停止或无法访问。这些故障通常是由网络连接问题或 AWS 依赖问题导致的。',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'MasterReachableFromNode',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 86400,
                    'Stat': 'Maximum',
                },
                'Label': domainName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1,
        ComparisonOperator='LessThanThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True    

def createThreadpoolWriteQueueAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-ThreadpoolWriteQueue-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(domain.get('TagList', []), 'ThreadpoolWriteQueue', 100)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'ElastiSearch集群{domainName}个节点平均索引队列长度大于阈值{threshold}。正在经历高索引并发。请检查和控制索引请求，或增加集群资源',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ThreadpoolWriteQueue',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': domainName,
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

def createAvgThreadpoolSearchQueueAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-AvgThreadpoolSearchQueue-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(domain.get('TagList', []), 'AvgThreadpoolSearchQueue', 500)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'ElastiSearch集群{domainName}个节点平均搜索队列长度大于阈值{threshold}。表示正在经历高搜索并发。请考虑扩展集群。您也可以增加搜索队列大小，但过度增加搜索队列大小可能会导致出现内存不足错误',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ThreadpoolSearchQueue',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': domainName,
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
    
def createMaxThreadpoolSearchQueueAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-MaxThreadpoolSearchQueue-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(domain.get('TagList', []), 'MaxThreadpoolSearchQueue', 5000)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'ElastiSearch集群{domainName}最大节点的搜索队列长度超出阈值{threshold}。表示正在经历高搜索并发。请考虑扩展集群。您也可以增加搜索队列大小，但过度增加搜索队列大小可能会导致出现内存不足错误',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ThreadpoolSearchQueue',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Maximum',
                },
                'Label': domainName,
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

def createThreadpoolSearchRejectedAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-ThreadpoolSearchRejected-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName} 搜索队列已满导致搜索请求被拒绝',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ThreadpoolSearchRejected',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'ReadThroughputMicroBursting',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'DIFF(m1)',
                'Label': domainName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True
    
def createThreadpoolWriteRejectedAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-ThreadpoolWriteRejected-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName} 索引队列已满导致写入索引请求被拒绝',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ThreadpoolWriteRejected',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': 'ReadThroughputMicroBursting',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'DIFF(m1)',
                'Label': domainName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def create5xxRateAlarm(region, domain, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    clientId = domain["DomainId"].split("/")[0]
    domainName = domain["DomainName"]
    alarmName = f'AWS/ES-5xxRate-{domainName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(domain.get('TagList', []), '5xxRate', 10)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'OpenSearch集群{domainName} 5xx错误率超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': '5xx',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'Label': '5xx',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'OpenSearchRequests',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'Label': 'OpenSearchRequests',
                'ReturnData': False,
            },
            {
                'Id': 'm3',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ES',
                        'MetricName': 'ElasticsearchRequests',
                        'Dimensions': [
                            {
                                'Name': 'ClientId',
                                'Value': clientId
                            },
                            {
                                'Name': 'DomainName',
                                'Value': domainName
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'Label': 'ElasticsearchRequests',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1/(m2+m3)*100',
                'Label': domainName,
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
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    instanceTypeMap = common.getInstanceTypes()
    numOfAlarmsCreated = 0
    alarmsDeleted = []
    for r in os.getenv('TargetRegions', os.getenv('AWS_REGION')).split(','):
        region = r.strip()
        logger.info(f'Remediating ES alarms in region {region}')
        # 获取所有ES集群
        client = boto3.client('es', region_name=region)
        response = client.list_domain_names()
        domainList = []
        for domain in response["DomainNames"]:
            domainList.append(domain)
        # 获取已创建的告警
        client = boto3.client('cloudwatch', region_name=region)
        paginator = client.get_paginator('describe_alarms')
        page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/ES-')
        alarmNames = []
        for page in page_iterator:
            alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))
    
        # 创建告警
        for domain in domainList:
            client = boto3.client('es', region_name=region)
            response = client.describe_elasticsearch_domain(DomainName=domain['DomainName'])
            domainStatus = response['DomainStatus']
            response = client.list_tags(ARN=domainStatus['ARN'])
            domainStatus['TagList'] = response['TagList']
            alarmName, created = createRedClusterAlarm(region, domainStatus, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createYellowClusterAlarm(region, domainStatus, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createClusterIndexWritesBlockedAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createFreeStorageSpaceAlarm(region, domainStatus, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createNodesAlarm(region, domainStatus, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createAutomatedSnapshotFailureAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createCPUUtilizationAlarm(region, domainStatus, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createJVMMemoryPressureAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createIopsAlarm(region, domainStatus, instanceTypeMap, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createThroughputAlarm(region, domainStatus, instanceTypeMap, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createActiveShardsAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createMasterReachableFromNodeAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createThreadpoolWriteQueueAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createAvgThreadpoolSearchQueueAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createMaxThreadpoolSearchQueueAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createThreadpoolSearchRejectedAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createThreadpoolWriteRejectedAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = create5xxRateAlarm(region, domainStatus, alarmNames)   
            numOfAlarmsCreated += 1 if created else 0
            
            # if domainStatus["ElasticsearchClusterConfig"]["InstanceType"].startswith('t'):
            #     alarmName, created = createCPUCreditBalanceAlarm(region, domainStatus, instanceTypeMap, alarmNames)   
            #     numOfAlarmsCreated += 1 if created else 0
            if domainStatus["EncryptionAtRestOptions"]["Enabled"]:
                alarmName, created = createKMSKeyErrorAlarm(region, domainStatus, alarmNames)
                numOfAlarmsCreated += 1 if created else 0
                alarmName, created = createKMSKeyInaccessibleAlarm(region, domainStatus, alarmNames)
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


