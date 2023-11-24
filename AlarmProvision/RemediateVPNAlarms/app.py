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

def createTunnelStateAlarm(connection, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    connectionId = connection["VpnConnectionId"]
    alarmName = f'AWS/VPN-TunnelState-{connectionId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    client = boto3.client('cloudwatch')
    response = client.put_metric_alarm(
        AlarmName=alarmName,
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
        TreatMissingData='breaching',
        Tags=[]
    )
    return alarmName, True

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    # 获取所有VPN连接
    client = boto3.client('ec2')
    response = client.describe_vpn_connections()
    logger.debug(f'Response of describe_vpn_connections: {response}')
    connections = []
    for c in response["VpnConnections"]:
        connections.append(c)
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    paginator = client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/VPN-')
    alarmNames = []
    for page in page_iterator:
        alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))
    # 创建告警
    numOfAlarmsCreated = 0
    for i in connections:
        alarmName, created = createTunnelStateAlarm(i, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
    # 删除不再使用的告警
    logger.info(f'Delete orphan alarms: {alarmNames}')
    for x in range(0, len(alarmNames), 100):
        response = client.delete_alarms(
            AlarmNames=alarmNames[x:x+100]
        )

    event["numOfAlarmsCreated"] = event.get("numOfAlarmsCreated", 0) + numOfAlarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmNames
    logger.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})


