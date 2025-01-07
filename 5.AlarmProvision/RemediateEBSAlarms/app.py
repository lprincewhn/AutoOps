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

def createStalledIOCheckAlarm(region, attachment, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    volId = attachment["VolumeId"]
    instanceId = attachment["InstanceId"]
    alarmName = f'AWS/EBS-VolumeStalledIOCheck-{volId}-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'EBS卷{volId}(EC实例{instanceId})IO阻塞检查失败',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EBS',
                        'MetricName': 'VolumeStalledIOCheck',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                            {
                                'Name': 'VolumeId',
                                'Value': volId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': volId,
                'ReturnData': True,
            }
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=0,
        ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createIopsAlarm(region, vol, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    volId = vol["VolumeId"]
    alarmName = f'AWS/EBS-IOPS-{volId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    base_iops = 0
    if vol["VolumeType"] == 'gp2':
        # 在最小 100 IOPS（33.33GiB 及以下）和最大 16,000 IOPS（5334GiB 及以上）之间，基准性能以每 GiB 卷大小 3 IOPS 的速度线性扩展。
        base_iops = max(min(vol["Size"]*3, 16000), 100)
    elif vol["VolumeType"] == 'io1':
        base_iops = vol["Iops"]
    elif vol["VolumeType"] == 'gp3':
        base_iops = max(vol["Iops"], 3000)
    if base_iops==0:
        return alarmName, False
    threshold = common.getThreshold(vol.get('Tags', []), 'IOPS', 0.8)*base_iops
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'EBS卷{volId} IOPS超过阈值{threshold}。EBS类型和性能参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EBS',
                        'MetricName': 'VolumeWriteOps',
                        'Dimensions': [
                            {
                                'Name': 'VolumeId',
                                'Value': volId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': volId,
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EBS',
                        'MetricName': 'VolumeReadOps',
                        'Dimensions': [
                            {
                                'Name': 'VolumeId',
                                'Value': volId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': volId,
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': '(m1+m2)/PERIOD(m1)',
                'Label': volId,
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

def createThroughputAlarm(region, vol, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch', region_name=region)
    volId = vol["VolumeId"]
    alarmName = f'AWS/EBS-Throughput-{volId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    base_throughput = 0
    if vol["VolumeType"] == 'gp2':
        # 吞吐量限制介于 128 MiB/s 和 250 MiB/s 之间，具体取决于卷大小。小于或等于 170 GiB 的卷提供最大 128 MiB/s 的吞吐量。如果有突增积分可用，大于 170 GiB 但小于 334 GiB 的卷将提供 250 的最大吞吐量。无论突增点数是多少，大于或等于 334 GiB 的卷均可提供 250 MiB/s。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/general-purpose.html
        if vol["Size"] >= 334:
            base_throughput = 250*1024*1024
        else:
            base_throughput = 128*1024*1024
    elif vol["VolumeType"] == 'io1':
        # 预置了最高 32000 IOPS 的 Provisioned IOPS SSD 卷支持 256 KiB 的最大 I/O 大小，可以达到最高 500 MiB/s 的吞吐量。当 I/O 大小达到最大时，吞吐量也将达到峰值 2000 IOPS。预置超过 32,000 IOPS（最高可达 64,000 IOPS）的卷以每预置 IOPS 16 KiB 的速率线性增加吞吐量。例如，预置了 48,000 IOPS 的卷可以支持高达 750 MiB/s 的吞吐量（每个预置 IOPS 16 KiB x 48,000 个预置 IOPS = 750 Mib/s）。要实现 1,000 MiB/s 的最大吞吐量，必须为卷预置 64,000 IOPS（每个预置 IOPS 16 KiB x 64,000 个预置 IOPS = 1,000 Mib/s）。https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/provisioned-iops.html
        base_throughput = max(vol["Iops"]*16*1024, 1000*1024*1024)
    elif vol["VolumeType"] == 'gp3':
        base_throughput = max(vol["Throughput"]*1024*1024, 125*1024*1024)
    if base_throughput==0:
        return alarmName, False
    threshold = common.getThreshold(vol.get('Tags', []), 'Throughput', 0.8)*base_throughput
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'EBS卷{volId}吞吐量超过阈值{threshold}Bytes/sec。EBS类型和性能参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EBS',
                        'MetricName': 'VolumeWriteBytes',
                        'Dimensions': [
                            {
                                'Name': 'VolumeId',
                                'Value': volId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': volId,
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EBS',
                        'MetricName': 'VolumeReadBytes',
                        'Dimensions': [
                            {
                                'Name': 'VolumeId',
                                'Value': volId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': volId,
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': '(m1+m2)/PERIOD(m1)',
                'Label': volId,
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
    numOfAlarmsCreated = 0
    alarmsDeleted = []
    for r in os.getenv('TargetRegions', os.getenv('AWS_REGION')).split(','):
        region = r.strip()
        logger.info(f'Remediating EBS alarms in region {region}')
        # 获取所有EBS实例
        client = boto3.client('ec2', region_name=region)
        paginator = client.get_paginator('describe_volumes')
        page_iterator = paginator.paginate()
        volList = []
        for page in page_iterator:
            for vol in page["Volumes"]:
                if vol["State"]=='in-use':
                    volList.append(vol)
        # 获取已创建的告警
        client = boto3.client('cloudwatch', region_name=region)
        paginator = client.get_paginator('describe_alarms')
        page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/EBS-')
        alarmNames = []
        for page in page_iterator:
            alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))
    
        # 创建告警
        for vol in volList:
            alarmName, created = createIopsAlarm(region, vol, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
            alarmName, created = createThroughputAlarm(region, vol, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
            for a in vol["Attachments"]:
                alarmName, created = createStalledIOCheckAlarm(region, a, alarmNames)
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


