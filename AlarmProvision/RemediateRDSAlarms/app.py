import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

def createCPUUtilizationAlarm(db, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-CPUUtilization-{dbId}'
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
        Threshold=80,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createCPUCreditBalanceAlarm(db, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-CPUCreditBalance-{dbId}'
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
        Threshold=60,
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createFreeStorageSpaceAlarm(db, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-FreeStorageSpace-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='磁盘空间不足',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
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
        Threshold=50*1024*1024*1024,
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createIopsAlarm(db, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-IOPS-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    base_iops = 0
    if db["StorageType"] == 'gp2':
        # 在最小 100 IOPS（33.33GiB 及以下）和最大 16,000 IOPS（5334GiB 及以上）之间，基准性能以每 GiB 卷大小 3 IOPS 的速度线性扩展。
        base_iops = max(min(db["storage_size"]*3, 16000), 100)
    elif db["StorageType"] == 'io1':
        base_iop1 = db["Iops"]
    elif db["StorageType"] == 'gp3':
        if db["AllocatedStorage"] >= 400:
            base_iops = max(db["Iops"], 12000)
        else:
            base_iops = 3000
    if base_iops==0:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='IOPS。EBS类型和性能参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
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
        Threshold=0.8*base_iops,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createThroughputAlarm(db, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    dbId = db["DBInstanceIdentifier"]
    alarmName = f'AWS/RDS-Throughput-{dbId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    base_throughput = 0
    if db["StorageType"] == 'gp2':
        # 吞吐量限制介于 128 MiB/s 和 250 MiB/s 之间，具体取决于卷大小。小于或等于 170 GiB 的卷提供最大 128 MiB/s 的吞吐量。如果有突增积分可用，大于 170 GiB 但小于 334 GiB 的卷将提供 250 的最大吞吐量。无论突增点数是多少，大于或等于 334 GiB 的卷均可提供 250 MiB/s。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/general-purpose.html
        if db["AllocatedStorage"] >= 334:
            base_throughput = 250*1024*1024
        else:
            base_throughput = 128*1024*1024
    elif db["StorageType"] == 'io1':
        # 预置了最高 32000 IOPS 的 Provisioned IOPS SSD 卷支持 256 KiB 的最大 I/O 大小，可以达到最高 500 MiB/s 的吞吐量。当 I/O 大小达到最大时，吞吐量也将达到峰值 2000 IOPS。预置超过 32,000 IOPS（最高可达 64,000 IOPS）的卷以每预置 IOPS 16 KiB 的速率线性增加吞吐量。例如，预置了 48,000 IOPS 的卷可以支持高达 750 MiB/s 的吞吐量（每个预置 IOPS 16 KiB x 48,000 个预置 IOPS = 750 Mib/s）。要实现 1,000 MiB/s 的最大吞吐量，必须为卷预置 64,000 IOPS（每个预置 IOPS 16 KiB x 64,000 个预置 IOPS = 1,000 Mib/s）。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/provisioned-iops.html
        base_throughput = max(db["Iops"]*16*1024, 32000)
    elif db["StorageType"] == 'gp3':
        if db["AllocatedStorage"] >= 400:
            base_throughput = max(db["StorageThroughput"]*1024*1024, 500*1024*1024)
        else:
            base_throughput = 125*1024*1024
    if base_throughput==0:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='吞吐量。EBS类型和性能参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
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
        Threshold=0.8*base_throughput,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    # 获取所有RDS实例
    client = boto3.client('rds')
    paginator = client.get_paginator('describe_db_instances')
    page_iterator = paginator.paginate()
    dbList = []
    for page in page_iterator:
        for db in page["DBInstances"]:
            dbList.append(db)
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    paginator = client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/RDS-')
    alarmNames = []
    for page in page_iterator:
        alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))

    # 创建告警
    numOfAlarmsCreated = 0
    for db in dbList:
        alarmName, created = createCPUUtilizationAlarm(db, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
        if db["DBInstanceClass"].startswith('db.t'):
            alarmName, created = createCPUCreditBalanceAlarm(db, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
        if not('aurora' in db["Engine"] or 'docdb' in db["Engine"]):
            alarmName, created = createFreeStorageSpaceAlarm(db, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
        alarmName, created = createIopsAlarm(db, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
        alarmName, created = createThroughputAlarm(db, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
            
    # 删除不再使用的告警
    logging.info(f'Delete orphan alarms: {alarmNames}')
    response = client.delete_alarms(
        AlarmNames=alarmNames
    )

    event["numOfAlarmsCreated"] = event.get("numOfAlarmsCreated", 0) + numOfAlarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmNames
    logging.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})


