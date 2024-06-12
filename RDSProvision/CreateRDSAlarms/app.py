import os
import boto3

def lambda_handler(event, context):
    print(f'Event In: {event}')
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic]
    client = ec2 = boto3.client('cloudwatch')
    dbInstanceIdentifier = event["dbInstanceIdentifier"]
    event['max_iops'] = 0
    if event["storage_type"] == 'gp2':
        # Refer to https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html#EBSVolumeTypes_gp2
        # 在最小 100 IOPS（33.33GiB 及以下）和最大 16,000 IOPS（5334GiB 及以上）之间，基准性能以每 GiB 卷大小 3 IOPS 的速度线性扩展。
        event['max_iops'] = max(min(event["storage_size"]*3, 16000), 100)
    elif event["storage_type"] == 'io1':
        event['max_iops'] = event["iops"]
    event['max_throughput'] = 0
    # Refer to https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html#solid-state-drives
    if event["storage_type"] == 'gp2':
        # 吞吐量限制介于 128 MiB/s 和 250 MiB/s 之间，具体取决于卷大小。小于或等于 170 GiB 的卷提供最大 128 MiB/s 的吞吐量。如果有突增积分可用，大于 170 GiB 但小于 334 GiB 的卷将提供 250 的最大吞吐量。无论突增点数是多少，大于或等于 334 GiB 的卷均可提供 250 MiB/s。除非您修改卷，否则在 2018 年 12 月 3 日之前创建并且自创建以来未修改过的 gp2 卷可能无法实现完全性能。
        if event["storage_size"] >= 334:
            event['max_throughput'] = 250*1024*1024
        else:
            event['max_throughput'] = 128*1024*1024
    elif event["storage_type"] == 'io1':
        # 只有在 IOPS 超过 32,000 的情况下，才能保证在 基于 Nitro 系统构建的实例上实现最大 IOPS 和吞吐量。其他实例保证最高为 32,000 IOPS 和 500 MiB/s。除非您修改卷，否则在 2017 年 12 月 6 日之前创建并且自创建以来未修改过的 io1 卷可能无法实现完全性能。
        event['max_throughput'] = 1000*1024*1024
    if event['max_iops']:
        response = client.put_metric_alarm(
            AlarmName=f'RDS-{dbInstanceIdentifier}-High-IOPS-Alarm',
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
                                    'Value': dbInstanceIdentifier
                                },
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Sum',
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
                                    'Value': dbInstanceIdentifier
                                },
                            ]
                        },
                        'Period': 300,
                        'Stat': 'Sum',
                    },
                    'Label': 'WriteIOPS',
                    'ReturnData': False,
                },
                {
                    'Id': 'e1',
                    'Expression': 'm1+m2',
                    'Label': 'IOPS',
                    'ReturnData': True
                },
            ],
            EvaluationPeriods=3,
            DatapointsToAlarm=3,
            Threshold=int(os.getenv('IOPS_Percentage_THreshold', '80'))*event['max_iops']/100,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='missing',
            Tags=[]
        )
        print(f'Response: {response}')
    if event['max_throughput']:
        response = client.put_metric_alarm(
            AlarmName=f'RDS-{dbInstanceIdentifier}-High-Throughput-Alarm',
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
                                    'Value': dbInstanceIdentifier
                                },
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Maximum',
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
                                    'Value': dbInstanceIdentifier
                                },
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Maximum',
                    },
                    'Label': 'WriteThroughput',
                    'ReturnData': False,
                },
                {
                    'Id': 'e1',
                    'Expression': 'm1+m2',
                    'Label': 'Throughput',
                    'ReturnData': True,
                    'Period': 300 
                },
            ],
            EvaluationPeriods=3,
            DatapointsToAlarm=3,
            Threshold=int(os.getenv('Throughput_Percentage_THreshold', '80'))*event['max_throughput']/100,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='missing',
            Tags=[]
        )
        print(f'Response: {response}')
    response = client.put_metric_alarm(
        AlarmName=f'RDS-{dbInstanceIdentifier}-High-CPUUtilization-Alarm',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        MetricName='CPUUtilization',
        Namespace='AWS/RDS',
        Statistic='Average',
        Dimensions=[{
            'Name': 'DBInstanceIdentifier',
            'Value': dbInstanceIdentifier
        }],
        Period=300,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=75,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    response = client.put_metric_alarm(
        AlarmName=f'RDS-{dbInstanceIdentifier}-High-SwapUsage-Alarm',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        MetricName='SwapUsage',
        Namespace='AWS/RDS',
        Statistic='Average',
        Dimensions=[{
            'Name': 'DBInstanceIdentifier',
            'Value': dbInstanceIdentifier
        }],
        Period=300,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=100*1024*1024,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    response = client.put_metric_alarm(
        AlarmName=f'RDS-{dbInstanceIdentifier}-Low-FreeStorageSpace-Alarm',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        MetricName='FreeStorageSpace',
        Namespace='AWS/RDS',
        Statistic='Average',
        Dimensions=[{
            'Name': 'DBInstanceIdentifier',
            'Value': dbInstanceIdentifier
        }],
        Period=60,
        EvaluationPeriods=5,
        DatapointsToAlarm=5,
        Threshold=50*1024*1024*1024,
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    return event
