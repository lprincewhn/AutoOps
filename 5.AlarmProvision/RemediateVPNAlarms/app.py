import os
import json
import boto3
import yaml
import logging
import common

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)
sts = boto3.client('sts')
account_id = sts.get_caller_identity()['Account']

def createTunnelStateAlarm(region, connection, tags, alarmExisting, alarmsCreated):
    populateAlarmDef(connection, tags, 'TunnelState')
    if not connection['AlarmDef']['Enabled']:
        return
    connectionId = connection["VpnConnectionId"]
    alarmName = f'AWS/VPN-TunnelState-{connectionId}'
    if alarmName in alarmExisting and connection['AlarmDef']['Enabled']:
        # 从现存告警列表中移除表示保留该告警
        logger.info(f'{alarmName} existed. skip it...')
        alarmExisting.remove(alarmName)
        return alarmName, False
    threshold = connection['AlarmDef']['Threshold']
    logger.info(f'Threshold of {alarmName}: {threshold}')
    alarm_actions, ok_actions = common.getSSMActions(account_id, region, connection['AlarmDef'])
    logger.info(f'AlarmActions of {alarmName}: {alarm_actions}')
    logger.info(f'OkActions of {alarmName}: {ok_actions}')

    client = boto3.client('cloudwatch', region_name=region)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='VPN隧道中断(平均值1表示连接总的两个隧道都健康，0.5表示只有一个隧道健康，0表示两个隧道的已经中断)',
        ActionsEnabled=True,
        AlarmActions=alarm_actions,
        OKActions=ok_actions,
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
        Threshold=threshold,
        ComparisonOperator='LessThanThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    alarmsCreated.append(alarmName)
    # return alarmName, True

alarmdef = None
def populateAlarmDef(alarmObject, tags, metricName):
    global alarmdef
    if not alarmdef:
        alarmdef_bucket = os.getenv('AlarmDefinitionBucket')
        alarmdef_file = 'vpn_alarms.yaml'
        client = boto3.client('s3')
        response = client.get_object(Bucket=alarmdef_bucket, Key=alarmdef_file)
        alarmdef = yaml.safe_load(response['Body'].read())
        
    for tag in tags:
        alarmObject[f'tag:{tag["Key"]}'] = tag['Value']
    matches = list(filter(lambda x:alarmObject.get(x['Key']) and alarmObject[x['Key']] in x['Value'], alarmdef['VPNAlarm']['Filters']))
    logger.info(f'Found {len(matches)} filters matched for metric {metricName}')
    alarmObject['AlarmDef'] = matches[0][metricName] if matches and matches[0].get(metricName)  else alarmdef['VPNAlarm']['Default'][metricName]
    logger.info(f'{alarmObject["AlarmDef"]}')
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    alarmsCreated = []
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
        for c in connections:
            logger.info(f'Remediating object: {c["VpnConnectionId"]}')
            c['Region'] = region
            # populateAlarmDef(c, c['Tags'], 'TunnelState')
            # if c['AlarmDef']['Enabled']:
            createTunnelStateAlarm(region, c, c['Tags'], alarmNames, alarmsCreated)
                # numOfAlarmsCreated += 1 if created else 0 
        # 删除不再使用的告警
        logger.info(f'Delete orphan alarms: {alarmNames}')
        for x in range(0, len(alarmNames), 100):
            response = client.delete_alarms(
                AlarmNames=alarmNames[x:x+100]
            )
        alarmsDeleted += map(lambda x: f'{region}:{x}', alarmNames)

    event["alarmsCreated"] = event.get("alarmsCreated", []) + alarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmsDeleted
    logger.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})


