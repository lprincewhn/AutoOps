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

def createCPUUtilizationAlarm(region, db, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-CPUUtilization-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(db.get("TagList"), "CPUUtilization", 80)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'RDS实例{dbId}CPU利用率超出阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': dbId,
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

def createCPUCreditBalanceAlarm(region, db, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-CPUCreditBalance-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    vcpus = instanceTypes[db["DBInstanceClass"].strip('db.')]["VCpuInfo"]["DefaultVCpus"]
    if not vcpus:
        return alarmName, False
    threshold = vcpus*common.getThreshold(db.get("TagList", []), "CreditSupportMinute", 80)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'RDS实例{dbId}CPU积分低于阈值{threshold} (1个CPU积分=1个vCPU*100%利用率*1分钟)。请参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html#key-concepts',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'CPUCreditBalance',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': dbId,
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

def createSwapUsageAlarm(region, db, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-SwapUsage-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(db.get("TagList"), "SwapUsageMB", 50)*1024*1024
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'RDS实例{dbId}Swap空间使用量超出阈值{threshold}, 开始使用SWAP空间通常表示内存不足',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'SwapUsage',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': dbId,
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
    
def createFreeStorageSpaceAlarm(region, db, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-FreeStorageSpace-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    threshold = common.getThreshold(db.get("TagList", []), "FreeStorageSpaceGB", 50)*1024*1024*1024
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'RDS实例{dbId}剩余磁盘空间低于{threshold/1024/1024/1024}GB',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'FreeStorageSpace',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            }
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': dbId,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=5,
        DatapointsToAlarm=5,
        Threshold=threshold,
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='ignore',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createIopsAlarm(region, db, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-IOPS-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    
    #实例侧限制
    instance_base_iops =  instance_max_iops = instance_threshold = 0   
    ebsOptimizedInfo = instanceTypes[db["DBInstanceClass"].strip('db.')]["EbsInfo"].get("EbsOptimizedInfo")
    if ebsOptimizedInfo:
        instance_base_iops=ebsOptimizedInfo["BaselineIops"]
        instance_max_iops=ebsOptimizedInfo["MaximumIops"]
        instance_threshold = common.getThreshold(db.get('TagList', []), 'MaxIOPS', 0.8)*instance_max_iops if instance_max_iops==instance_base_iops else common.getThreshold(db.get('TagList', []), 'BaseIOPS', 1)*instance_base_iops
        logger.info(f'Instance Base IOPS: {instance_base_iops}, Max IOPS: {instance_max_iops}, Threshold={instance_threshold}')   

    #存储侧限制, Aurora和DocumentDB无此限制
    ebs_base_iops = ebs_max_iops = ebs_threshold = 10000000000000
    if not('aurora' in db["Engine"] or 'docdb' in db["Engine"]):
        if db["StorageType"] == 'gp2':
            # 在最小 100 IOPS（33.33GiB 及以下）和最大 16,000 IOPS（5334GiB 及以上）之间，基准性能以每 GiB 卷大小 3 IOPS 的速度线性扩展。
            ebs_base_iops = max(min(db["storage_size"]*3, 16000), 100)
            ebs_max_iops = max(12000 if db["AllocatedStorage"] >= 400 else 3000, ebs_base_iops) 
        elif db["StorageType"] == 'io1':
            ebs_base_iops = ebs_max_iops = db["Iops"]
        elif db["StorageType"] == 'gp3':
            if db["AllocatedStorage"] >= 400:
                ebs_base_iops = ebs_max_iops = max(db["Iops"], 12000)
            else:
                ebs_base_iops = ebs_max_iops = max(db["Iops"], 3000)
        ebs_threshold = common.getThreshold(db.get('TagList', []), 'MaxIOPS', 0.8)*ebs_max_iops if ebs_max_iops==ebs_base_iops else common.getThreshold(db.get('TagList', []), 'BaseIOPS', 1)*ebs_base_iops
        logger.info(f'EBS Base IOPS: {ebs_base_iops}, Max IOPS: {ebs_max_iops}, Threshold: {ebs_threshold}')  

    threshold = min(instance_threshold, ebs_threshold)   
    if threshold==0:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'RDS实例{dbId} IOPS超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'ReadIOPS',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': 'ReadIOPS',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'WriteIOPS',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': 'WriteIOPS',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1+m2',
                'Label': dbId,
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

def createThroughputAlarm(region, db, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-Throughput-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
        
    #实例侧限制
    instance_base_throughput =  instance_max_throughput = instance_threshold = 0   
    ebsOptimizedInfo = instanceTypes[db["DBInstanceClass"].strip('db.')]["EbsInfo"].get("EbsOptimizedInfo")
    if ebsOptimizedInfo:
        instance_base_throughput=ebsOptimizedInfo["BaselineBandwidthInMbps"]*1000*1000/8
        instance_max_throughput=ebsOptimizedInfo["MaximumBandwidthInMbps"]*1000*1000/8
        instance_threshold = common.getThreshold(db.get('TagList', []), 'MaxThroughput', 0.8)*instance_max_throughput if instance_max_throughput==instance_base_throughput else common.getThreshold(db.get('TagList', []), 'BaseThroughput', 1)*instance_base_throughput
        logger.info(f'Instance Base Throughput: {instance_base_throughput}, Max Throughput: {instance_max_throughput}, Threshold={instance_threshold}')   

    #存储侧限制, Aurora和DocumentDB无此限制
    ebs_base_throughput = ebs_max_throughput = ebs_threshold = 100000*1024*1024
    if not('aurora' in db["Engine"] or 'docdb' in db["Engine"]):
        if db["StorageType"] == 'gp2':
            # 吞吐量限制介于 128 MiB/s 和 250 MiB/s 之间，具体取决于卷大小。小于或等于 170 GiB 的卷提供最大 128 MiB/s 的吞吐量。如果有突增积分可用，大于 170 GiB 但小于 334 GiB 的卷将提供 250 的最大吞吐量。无论突增点数是多少，大于或等于 334 GiB 的卷均可提供 250 MiB/s。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/general-purpose.html
            if db["AllocatedStorage"] >= 334:
                ebs_base_throughput = ebs_max_throughput = 250*1024*1024
            elif db["AllocatedStorage"] >= 170:
                ebs_max_throughput = 250*1024*1024       
                ebs_base_throughput = 0.2 * ebs_max_throughput
            else:
                ebs_max_throughput = 128*1024*1024
                ebs_base_throughput = 0.2 * ebs_max_throughput
        elif db["StorageType"] == 'io1':
            # 预置了最高 32000 IOPS 的 Provisioned IOPS SSD 卷支持 256 KiB 的最大 I/O 大小，可以达到最高 500 MiB/s 的吞吐量。当 I/O 大小达到最大时，吞吐量也将达到峰值 2000 IOPS。预置超过 32,000 IOPS（最高可达 64,000 IOPS）的卷以每预置 IOPS 16 KiB 的速率线性增加吞吐量。例如，预置了 48,000 IOPS 的卷可以支持高达 750 MiB/s 的吞吐量（每个预置 IOPS 16 KiB x 48,000 个预置 IOPS = 750 Mib/s）。要实现 1,000 MiB/s 的最大吞吐量，必须为卷预置 64,000 IOPS（每个预置 IOPS 16 KiB x 64,000 个预置 IOPS = 1,000 Mib/s）。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/provisioned-iops.html
            ebs_max_throughput = ebs_base_throughput = max(db["Iops"]*16*1024, 1000*1024*1024)
        elif db["StorageType"] == 'gp3':
            if db["AllocatedStorage"] >= 400:
                ebs_max_throughput = ebs_base_throughput = max(db.get("StorageThroughput", 0)*1024*1024, 500*1024*1024)
            else:
                ebs_max_throughput = ebs_base_throughput = max(db.get("StorageThroughput", 0)*1024*1024, 125*1024*1024) 
            ebs_threshold = common.getThreshold(db.get('TagList', []), 'MaxThroughput', 0.8)*ebs_max_throughput if ebs_max_throughput==ebs_base_throughput else common.getThreshold(db.get('TagList', []), 'BaseThroughput', 1)*ebs_base_throughput
            logger.info(f'EBS Base Throughput: {ebs_base_throughput}, Max Throughput: {ebs_max_throughput}, Threshold={ebs_threshold}') 
    
    threshold = min(instance_threshold, ebs_threshold)   
    if threshold==0:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'RDS实例{dbId} IO吞吐量超过阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'ReadThroughput',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': 'ReadThroughput',
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'WriteThroughput',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': 'WriteThroughput',
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'm1+m2',
                'Label': dbId,
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

def createInstanceNetworkBandwidthlarm(region, db, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-NetworkBandwidth-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    baselineBandwidthInGbps = instanceTypes[db["DBInstanceClass"].strip('db.')]["NetworkInfo"]["NetworkCards"][0].get("BaselineBandwidthInGbps")
    maxBandwidthInGbps = instanceTypes[db["DBInstanceClass"].strip('db.')]["NetworkInfo"]["NetworkCards"][0].get("PeakBandwidthInGbps")
    if not baselineBandwidthInGbps:
        return alarmName, False
    base_throughput=baselineBandwidthInGbps*1000*1000*1000/8
    max_throughput=maxBandwidthInGbps*1000*1000*1000/8
    threshold = common.getThreshold(db.get('TagList', []), 'MaxNetworkBandwidth', 1)*max_throughput if max_throughput==base_throughput else common.getThreshold(db.get('TagList', []), 'BaseNetworkBandwidth', 1)*base_throughput
    logger.info(f'Network Base Throughput: {base_throughput}, Max Throughput: {max_throughput}, Threshold: {threshold}')
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'RDS实例{dbId}网络带宽超出阈值{threshold} Bytes/sec。参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/instance-types.html#instance-type-summary-table。对于不可突增实例（基线性能等于最大性能），告警阈值为限制的的80%，对于可突增实例（基准性能低于最大性能, 通常，有 16 个或更少 vCPU 的实例（大小为 4xlarge 或更小）被记录为具有“高达”的指定带宽；例如，“高达 10 Gbps”。这些实例具备基准带宽。为满足其他需求，可以使用网络 I/O 积分机制，以突增超出其基准带宽。实例可以在有限时间内使用突增带宽，通常为5到60分钟，具体取决于实例的大小。），告警阈值为基线性能',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'NetworkReceiveThroughput',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': dbId,
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'NetworkTransmitThroughput',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': dbId,
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'MAX([m1,m2])',
                'Label': dbId,
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

def createDatabaseConnectionsAlarm(region, db, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-DatabaseConnections-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
        
    memory = instanceTypes[db["DBInstanceClass"].strip('db.')]["MemoryInfo"]["SizeInMiB"]
    threshold = int(common.getThreshold(db.get("TagList"), "DatabaseConnections", 0.9*(memory-500)*1024*1024/12582880))
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'RDS实例{dbId}数据库连接数超出阈值{threshold}',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/RDS',
                        'MetricName': 'DatabaseConnections',
                        'Dimensions': [
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': dbId
                            }
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': dbId,
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
        logger.info(f'Remediating RDS alarms in region {region}')
        # 获取所有RDS实例
        client = boto3.client('rds', region_name=region)
        paginator = client.get_paginator('describe_db_instances')
        page_iterator = paginator.paginate()
        dbList = []
        for page in page_iterator:
            for db in page["DBInstances"]:
                dbList.append(db)
        # 获取已创建的告警
        client = boto3.client('cloudwatch', region_name=region)
        paginator = client.get_paginator('describe_alarms')
        page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/RDS-')
        alarmNames = []
        for page in page_iterator:
            alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))
    
        # 创建告警
        for db in dbList:
            alarmName, created = createCPUUtilizationAlarm(region, db, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createSwapUsageAlarm(region, db, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createIopsAlarm(region, db, instanceTypeMap, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
            alarmName, created = createThroughputAlarm(region, db, instanceTypeMap, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createInstanceNetworkBandwidthlarm(region, db, instanceTypeMap, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createDatabaseConnectionsAlarm(region, db, instanceTypeMap, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            if db["DBInstanceClass"].startswith('db.t'):
                alarmName, created = createCPUCreditBalanceAlarm(region, db, instanceTypeMap, alarmNames)
                numOfAlarmsCreated += 1 if created else 0 
            if not('aurora' in db["Engine"] or 'docdb' in db["Engine"]):
                alarmName, created = createFreeStorageSpaceAlarm(region, db, alarmNames)
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


