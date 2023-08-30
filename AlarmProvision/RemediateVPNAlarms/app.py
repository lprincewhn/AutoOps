import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

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
    logging.info(f'Event In: {json.dumps(event)}')
    # 获取所有VPN连接
    client = boto3.client('ec2')
    response = client.describe_vpn_connections()
    logging.debug(f'Response of describe_vpn_connections: {response}')
    connections = []
    for c in response["VpnConnections"]:
        connections.append(c)
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    response = client.describe_alarms(
        AlarmNamePrefix=f'AWS/VPN-'
    )
    alarmNames = list(map(lambda x:x.get('AlarmName'), response['MetricAlarms']))
    # 创建告警
    numOfAlarmsCreated = 0
    for i in connections:
        alarmName, created = createTunnelStateAlarm(i, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
    # 删除不再使用的告警
    logging.info(f'Delete orphan alarms: {alarmNames}')
    for x in range(0, len(alarmNames), 100):
        response = client.delete_alarms(
            AlarmNames=alarmNames[x:x+100]
        )

    event["numOfAlarmsCreated"] = event.get("numOfAlarmsCreated", 0) + numOfAlarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmNames
    logging.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})


