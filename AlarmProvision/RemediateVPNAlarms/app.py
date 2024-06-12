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

def createTunnelStateAlarm(region, connection, alarmNames):
    # OpsItem Categories: availability, cost, performance, recovery, security.
    actions = [f'arn:aws:ssm:{region}:{os.getenv("AWSAccountId")}:opsitem:severity#CATEGORY=availability']
    if os.getenv("SNSTopicName"):
        sns_topic = f'arn:aws:sns:{region}:{os.getenv("AWSAccountId")}:{os.getenv("SNSTopicName")}'
        actions.append(sns_topic)
        print(sns_topic)
        
    actions_enable = bool(actions)
    connectionId = connection["VpnConnectionId"]
    alarmName = f'AWS/VPN-TunnelState-{connectionId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    client = boto3.client('cloudwatch', region_name=region)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='VPN隧道中断(平均值1表示连接总的两个隧道都健康，0.5表示只有一个隧道健康，0表示两个隧道的已经中断)',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/VPN',
                        'MetricName': 'TunnelState',
                        'Dimensions': [
                            {
                                'Name': 'VpnId',
                                'Value': connectionId
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': connectionId,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=1,
        ComparisonOperator='LessThanThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    return alarmName, True

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    numOfAlarmsCreated = 0
    alarmsDeleted = []
    for r in os.getenv('TargetRegions', os.getenv('AWS_REGION')).split(','):
        region = r.strip()
        logger.info(f'Remediating VPN alarms in region {region}')
        # 获取所有VPN连接
        client = boto3.client('ec2', region_name=region)
        response = client.describe_vpn_connections()
        logger.debug(f'Response of describe_vpn_connections: {response}')
        connections = []
        for c in response["VpnConnections"]:
            connections.append(c)
        # 获取已创建的告警
        client = boto3.client('cloudwatch', region_name=region)
        paginator = client.get_paginator('describe_alarms')
        page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/VPN-')
        alarmNames = []
        for page in page_iterator:
            alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))
        # 创建告警
        for i in connections:
            alarmName, created = createTunnelStateAlarm(region, i, alarmNames)
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


