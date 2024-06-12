import os
import json
import boto3
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')

    event['max_iops'] = 0
    if event["volumeType"] == 'gp2':
        # Refer to https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html#EBSVolumeTypes_gp2
        # 在最小 100 IOPS（33.33GiB 及以下）和最大 16,000 IOPS（5334GiB 及以上）之间，基准性能以每 GiB 卷大小 3 IOPS 的速度线性扩展。
        event['max_iops'] = max(min(event["storage_size"]*3, 16000), 100)
    elif event["volumeType"] in ['gp3', 'io1', 'io2']:
        event['max_iops'] = event["iops"]

    event['max_throughput'] = 0
    # Refer to https://docs.aws.amazon.com/zh_cn/AWSEC2/latest/UserGuide/ebs-volume-types.html#solid-state-drives
    if event["volumeType"] == 'gp2':
        # 吞吐量限制介于 128 MiB/s 和 250 MiB/s 之间，具体取决于卷大小。小于或等于 170 GiB 的卷提供最大 128 MiB/s 的吞吐量。如果有突增积分可用，大于 170 GiB 但小于 334 GiB 的卷将提供 250 的最大吞吐量。无论突增点数是多少，大于或等于 334 GiB 的卷均可提供 250 MiB/s。除非您修改卷，否则在 2018 年 12 月 3 日之前创建并且自创建以来未修改过的 gp2 卷可能无法实现完全性能。
        if event["size"] >= 334:
            event['max_throughput'] = 250*1024*1024
        else:
            event['max_throughput'] = 128*1024*1024
    elif event["volumeType"] == 'io1':
        # 只有在 IOPS 超过 32,000 的情况下，才能保证在 基于 Nitro 系统构建的实例上实现最大 IOPS 和吞吐量。其他实例保证最高为 32,000 IOPS 和 500 MiB/s。除非您修改卷，否则在 2017 年 12 月 6 日之前创建并且自创建以来未修改过的 io1 卷可能无法实现完全性能。
        if event['iops'] > 32000:
            event['max_throughput'] = 1000*1024*1024
        else:
            event['max_throughput'] = 500*1024*1024

    client = boto3.client('cloudwatch')
    if event['max_iops']:
        response = client.put_metric_alarm(
            AlarmName=f'EBS-{event.get("volumeId")}-High-IOPS-Alarm',
            ActionsEnabled=False,
            Metrics=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EBS',
                            'MetricName': 'VolumeReadOps',
                            'Dimensions': [
                                {
                                    'Name': 'VolumeId',
                                    'Value': event.get('volumeId') 
                                },
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Sum',
                    },
                    'Label': 'VolumeReadOps',
                    'ReturnData': False,
                },
                {
                    'Id': 'm2',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EBS',
                            'MetricName': 'VolumeWriteOps',
                            'Dimensions': [
                                {
                                    'Name': 'VolumeId',
                                    'Value': event.get('volumeId')
                                },
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Sum',
                    },
                    'Label': 'VolumeWriteOps',
                    'ReturnData': False,
                },
                {
                    'Id': 'e1',
                    'Expression': '(m1+m2)/period(m1)',
                    'Label': 'IOPS',
                    'ReturnData': True,
                    'Period': 60
                },
            ],
            EvaluationPeriods=5,
            DatapointsToAlarm=5,
            Threshold=int(os.getenv('IOPS_Percentage_Threshold', '80'))*event['max_iops']/100,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='missing',
            Tags=[]
        )
        logger.debug(f'Response: {response}')
    if event['max_throughput']:
        response = client.put_metric_alarm(
            AlarmName=f'EBS-{event.get("volumeId")}-High-Throughput-Alarm',
            ActionsEnabled=False,
            Metrics=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EBS',
                            'MetricName': 'VolumeReadBytes',
                            'Dimensions': [
                                {
                                    'Name': 'VolumeId',
                                    'Value': event.get('volumeId')
                                },
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Sum',
                    },
                    'Label': 'ReadBytes',
                    'ReturnData': False,
                },
                {
                    'Id': 'm2',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EBS',
                            'MetricName': 'VolumeWriteBytes',
                            'Dimensions': [
                                {
                                    'Name': 'VolumeId',
                                    'Value': event.get('volumeId')
                                },
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Sum',
                    },
                    'Label': 'WriteBytes',
                    'ReturnData': False,
                },
                {
                    'Id': 'e1',
                    'Expression': '(m1+m2)*8/period(m1)',
                    'Label': 'Throughput',
                    'ReturnData': True,
                    'Period': 60
                },
            ],
            EvaluationPeriods=1,
            DatapointsToAlarm=1,
            Threshold=int(os.getenv('Throughput_Percentage_THreshold', '80'))*event['max_throughput']/100,
            ComparisonOperator='GreaterThanOrEqualToThreshold',
            TreatMissingData='missing',
            Tags=[]
        )
        logger.info(f'Response: {response}')
    return event
