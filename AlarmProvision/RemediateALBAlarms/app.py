import os
import json
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)

def createUnHealthyHostCountAlarm(tg, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    lbName = '/'.join(tg[0].split(':')[5].split('/')[1:])
    tgName = tg[1]
    alarmName = f'AWS/ALB-UnHealthyHostCount-{lbName}-{tgName}'
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
                        'Namespace': 'AWS/ApplicationELB',
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
    return alarmName, True

def createTargetResponseTimeAlarm(tg, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    lbName = '/'.join(tg[0].split(':')[5].split('/')[1:])
    tgName = tg[1]
    alarmName = f'AWS/ALB-TargetResponseTime-{lbName}-{tgName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='请求离开负载均衡器直至收到来自目标的响应所用的时间（以秒为单位）。这与访问日志中的 target_processing_time 字段是等效的。',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ApplicationELB',
                        'MetricName': 'TargetResponseTime',
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
                    'Period': 300,
                    'Stat': 'Average',
                },
                'Label': tgName,
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=0.1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    return alarmName, True

def createHTTPCode_Target_5XX_RateAlarm(lb, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    lbName = '/'.join(lb.split(':')[5].split('/')[1:])
    alarmName = f'AWS/ALB-HTTPCode_Target_5XX_Rate-{lbName}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription='目标生成的HTTP响应代码的数量占已转发给目标请求数的比例。它不包括负载均衡器生成的任何响应代码。',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/ApplicationELB',
                        'MetricName': 'HTTPCode_Target_5XX_Count',
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
                        'Namespace': 'AWS/ApplicationELB',
                        'MetricName': 'RequestCount',
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
    return alarmName, True

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    # 获取所有ALB目标组
    client = boto3.client('elbv2')
    paginator = client.get_paginator('describe_target_groups')
    page_iterator = paginator.paginate()
    logger.debug(f'Response of describe_alarms: {page_iterator}')
    targetGroups = []
    for page in page_iterator:
        for tg in page["TargetGroups"]:
            if tg["LoadBalancerArns"] and 'app' in tg["LoadBalancerArns"][0]:
                targetGroups.append((tg["LoadBalancerArns"][0], tg["TargetGroupName"]))
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    paginator = client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/ALB-')
    logger.debug(f'Response of describe_alarms: {page_iterator}')
    alarmNames = []
    for page in page_iterator:
        alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))

    # 创建告警
    numOfAlarmsCreated = 0
    for tg in targetGroups:
        alarmName, created = createUnHealthyHostCountAlarm(tg, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
        alarmName, created = createTargetResponseTimeAlarm(tg, alarmNames)
        numOfAlarmsCreated += 1 if created else 0
            
    for lb in set(map(lambda x:x[0], targetGroups)):
        alarmName, created = createHTTPCode_Target_5XX_RateAlarm(lb, alarmNames)
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


