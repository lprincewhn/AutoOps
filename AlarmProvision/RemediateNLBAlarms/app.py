import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

def createUnHealthyHostCountAlarm(tg, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    lbName = '/'.join(tg[0].split(':')[5].split('/')[1:])
    tgName = tg[1]
    alarmName = f'AWS/NLB-UnHealthyHostCount-{lbName}-{tgName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='未正常运行的目标数量',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/NetworkELB',
                        'MetricName': 'UnHealthyHostCount',
                        'Dimensions': [
                            {
                                'Name': 'LoadBalancer',
                                'Value': lbName
                            },
                            {
                                'Name': 'TargetGroup',
                                'Value': tgName
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Average',
                },
                'Label': tgName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createTCP_Target_Reset_RateAlarm(lb, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    lbName = '/'.join(lb.split(':')[5].split('/')[1:])
    alarmName = f'AWS/NLB-TCP_Target_Reset_Rate-{lbName}'
    print(alarmNames, alarmName)
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='从目标发送至客户端的重置(RST)数据包的数量占新增连接数比例。这些重置由目标生成，然后由负载均衡器转发。',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/NetworkELB',
                        'MetricName': 'TCP_Target_Reset_Count',
                        'Dimensions': [
                            {
                                'Name': 'LoadBalancer',
                                'Value': lbName
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'Label': lbName,
                'ReturnData': False,
            },
            {
                'Id': 'm2',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/NetworkELB',
                        'MetricName': 'NewFlowCount',
                        'Dimensions': [
                            {
                                'Name': 'LoadBalancer',
                                'Value': lbName
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Sum',
                },
                'Label': lbName,
                'ReturnData': False,
            },
            {
                'Id': 'm3',
                'Expression': 'm1/m2*100',
                'Label': lbName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    # 获取所有NLB标组
    client = boto3.client('elbv2')
    paginator = client.get_paginator('describe_target_groups')
    page_iterator = paginator.paginate()
    logging.debug(f'Response of describe_alarms: {page_iterator}')
    targetGroups = []
    for page in page_iterator:
        for tg in page["TargetGroups"]:
            if tg["LoadBalancerArns"] and 'net' in tg["LoadBalancerArns"][0]:
                targetGroups.append((tg["LoadBalancerArns"][0], tg["TargetGroupName"]))
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    paginator = client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/NLB-')
    logging.debug(f'Response of describe_alarms: {page_iterator}')
    alarmNames = []
    for page in page_iterator:
        alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))

    # 创建告警
    numOfAlarmsCreated = 0
    for tg in targetGroups:
        alarmName, created = createUnHealthyHostCountAlarm(tg, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
    for lb in set(map(lambda x:x[0], targetGroups)):
        alarmName, created = createTCP_Target_Reset_RateAlarm(lb, alarmNames)
        numOfAlarmsCreated += 1 if created else 0
            
    # 删除不再使用的告警
    logging.info(f'Delete orphan alarms: {alarmNames}')
    response = client.delete_alarms(
        AlarmNames=alarmNames
    )
    logging.debug(f'Response of delete_alarms: {response}')

    event["numOfAlarmsCreated"] = event.get("numOfAlarmsCreated", 0) + numOfAlarmsCreated
    event["alarmsDeleted"] = event.get("alarmsDeleted", []) + alarmNames
    logging.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})


