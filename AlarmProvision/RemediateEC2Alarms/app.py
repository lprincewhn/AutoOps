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

def createCPUUtilizationAlarm(instance, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    instanceId = instance["InstanceId"]
    alarmName = f'AWS/EC2-CPUUtilization-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription="CPU利用率过高",
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': instanceId,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=common.getThreshold(instance.get('Tags', []), 'CPUUtilization', 80),
        ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createStatusCheckFailed_SystemAlarm(instance, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    region = os.getenv('AWS_REGION')
    actions_enable = (sns_topic!=None) 
    actions = [f'arn:aws:automate:{region}:ec2:recover', sns_topic] if sns_topic else [f'arn:aws:automate:{region}:ec2:recover']
    client = boto3.client('cloudwatch')
    instanceId = instance["InstanceId"]
    alarmName = f'AWS/EC2-StatusCheckFailed_System-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription="系统健康检查失败，表示底层宿主机硬件故障。对于支持“自动恢复“的机型已经触发自动恢复，请检查实例和系统状态。对于不支持“自动恢复”的机型，需要强制停止(Stop)，然后再启动(Start)。上述操作将使实例漂移到健康的宿主机上。系统启动后请登陆系统检查应用情况。",
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'StatusCheckFailed_System',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': instanceId,
                'ReturnData': True,
            },
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

def createStatusCheckFailed_InstanceAlarm(instance, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    instanceId = instance["InstanceId"]
    alarmName = f'AWS/EC2-StatusCheckFailed_Instance-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription="实例健康检查失败，表示实例网络不可用(ARP检测无响应)。可能是操作系统网络进程异常或者重要配置文件出错导致，重启(Restart)可解决网络进程异常问题。",
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'StatusCheckFailed_Instance',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': instanceId,
                'ReturnData': True,
            },
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

def createCPUCreditBalanceAlarm(instance, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    instanceId = instance["InstanceId"]
    alarmName = f'AWS/EC2-CPUCreditBalance-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    vcpus = instance["CpuOptions"]["CoreCount"]*instance["CpuOptions"]["ThreadsPerCore"]
    if not vcpus:
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription="T系列机器CPU积分不足(1个CPU积分=1个vCPU*100%利用率*1分钟)。请参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html#key-concepts",
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'CPUCreditBalance',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': instanceId,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=vcpus*common.getThreshold(instance.get('Tags', []), 'CreditSupportMinute', 30),
        ComparisonOperator='LessThanThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createInstanceEBSIOPSAlarm(instance, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    instanceId = instance["InstanceId"]
    alarmName = f'AWS/EC2-EBSIOPS-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    ebsOptimizedInfo = instanceTypes[instance["InstanceType"]]["EbsInfo"].get("EbsOptimizedInfo")
    if not ebsOptimizedInfo:
        return alarmName, False
    base_iops=ebsOptimizedInfo["BaselineIops"]
    max_iops=ebsOptimizedInfo["MaximumIops"]
    threshold = common.getThreshold(instance.get('Tags', []), 'MaxIOPS', 0.8)*max_iops if max_iops==base_iops else common.getThreshold(instance.get('Tags', []), 'BaseIOPS', 1)*base_iops
    logger.info(f'EBS Base IOPS: ${base_iops}, Max IOPS: {max_iops}, Threshold: {threshold}')
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='实例侧IOPS限制，参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-optimized.html#current-general-purpose。对于不可突增实例（基线性能等于最大性能），告警阈值为限制的的80%，对于可突增实例（基准性能低于最大性能, 每24小时支持一次30分钟的最大性能，之后会恢复到基线性能），告警阈值为基线性能',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'EBSReadOps',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': instanceId,
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'EBSWriteOps',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': instanceId,
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': '(m1+m2)/PERIOD(m1)',
                'Label': instanceId,
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
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createInstanceEBSThroughputlarm(instance, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    instanceId = instance["InstanceId"]
    alarmName = f'AWS/EC2-EBSThroughput-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    ebsOptimizedInfo = instanceTypes[instance["InstanceType"]]["EbsInfo"].get("EbsOptimizedInfo")
    if not ebsOptimizedInfo:
        return alarmName, False
    base_throughput=ebsOptimizedInfo["BaselineThroughputInMBps"]*1000*1000/8
    max_throughput=ebsOptimizedInfo["MaximumBandwidthInMbps"]*1000*1000/8
    threshold = common.getThreshold(instance.get('Tags', []), 'MaxThroughput', 0.8)*max_throughput if max_throughput==base_throughput else common.getThreshold(instance.get('Tags', []), 'BaseThroughput', 1)*base_throughput
    logger.info(f'EBS Base Throughput: ${base_throughput}, Max Throughput: {max_throughput}, Threshold: {threshold}')
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='实例侧IO吞吐量限制，参考：https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-optimized.html#current-general-purpose。对于不可突增实例（基线性能等于最大性能），告警阈值为限制的的80%，对于可突增实例（基准性能低于最大性能, 每24小时支持一次30分钟的最大性能，之后会恢复到基线性能），告警阈值为基线性能',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'EBSReadBytes',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': instanceId,
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'EBSWriteBytes',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': instanceId,
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': '(m1+m2)/PERIOD(m1)',
                'Label': instanceId,
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
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createInstanceNetworkBandwidthlarm(instance, instanceTypes, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    instanceId = instance["InstanceId"]
    alarmName = f'AWS/EC2-NetworkBandwidth-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    baselineBandwidthInGbps = instanceTypes[instance["InstanceType"]]["NetworkInfo"]["NetworkCards"][0].get("BaselineBandwidthInGbps")
    maxBandwidthInGbps = instanceTypes[instance["InstanceType"]]["NetworkInfo"]["NetworkCards"][0].get("PeakBandwidthInGbps")
    if not baselineBandwidthInGbps:
        return alarmName, False
    base_throughput=baselineBandwidthInGbps*1000*1000*1000/8
    max_throughput=maxBandwidthInGbps*1000*1000*1000/8
    threshold = common.getThreshold(instance.get('Tags', []), 'MaxNetworkBandwidth', 0.8)*max_throughput if max_throughput==base_throughput else common.getThreshold(instance.get('Tags', []), 'BaseNetworkBandwidth', 1)*base_throughput
    logger.info(f'Network Base Throughput: {base_throughput}, Max Throughput: {max_throughput}, Threshold: {threshold}')
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
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'NetworkIn',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': instanceId,
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'NetworkOut',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': instanceId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Sum',
                },
                'Label': instanceId,
                'ReturnData': False,
            },
            {
                'Id': 'e1',
                'Expression': 'MAX([m1,m2])/PERIOD(m1)',
                'Label': instanceId,
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
    logger.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    instanceTypeMap = common.getInstanceTypes()
    # 获取所有EC2实例
    client = boto3.client('ec2')
    paginator = client.get_paginator('describe_instances')
    page_iterator = paginator.paginate()
    instanceList = []
    for page in page_iterator:
        for r in page["Reservations"]:
            for i in r["Instances"]:
                instanceList.append(i)
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    response = client.describe_alarms(
        AlarmNamePrefix=f'AWS/EC2-'
    )
    alarmNames = list(map(lambda x:x.get('AlarmName'), response['MetricAlarms']))
    # 创建告警
    numOfAlarmsCreated = 0
    for i in instanceList:
        alarmName, created = createCPUUtilizationAlarm(i, alarmNames)
        numOfAlarmsCreated += 1 if created else 0
        alarmName, created = createInstanceEBSIOPSAlarm(i, instanceTypeMap, alarmNames)
        numOfAlarmsCreated += 1 if created else 0
        alarmName, created = createInstanceEBSThroughputlarm(i, instanceTypeMap, alarmNames)
        numOfAlarmsCreated += 1 if created else 0
        alarmName, created = createInstanceNetworkBandwidthlarm(i, instanceTypeMap, alarmNames)
        numOfAlarmsCreated += 1 if created else 0
        if i["InstanceType"].startswith("t"):
            alarmName, created = createCPUCreditBalanceAlarm(i, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
        try:
            alarmName, created = createStatusCheckFailed_SystemAlarm(i, alarmNames)
            numOfAlarmsCreated += 1 if created else 0
            alarmName, created = createStatusCheckFailed_InstanceAlarm(i, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
        except Exception as e:
            logger.warning(f'{e}')
    # 删除不再使用的告警
    logger.info(f'Delete orphan alarms: {alarmNames}')
    for x in range(0, len(alarmNames), 100):
        response = client.delete_alarms(
            AlarmNames=alarmNames[x:x+100]
        )
    logger.debug(f'Response of delete_alarms: {response}')

    event["numOfAlarmsCreated"] = event.get("numOfAlarmsCreated", 0) + numOfAlarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmNames
    logger.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    print(lambda_handler({}, {}))


