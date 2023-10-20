import os
import json
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)

def getThreshold(tags, metric, default):
    thresholds = list(filter(lambda x:x.get("Key")=='AlarmThreshold', tags))
    threshold = default
    try:
        threshold = json.loads(thresholds[0].get("Value"))[metric]
        logger.info(f"Set threshold of {metric} according 'AlarmThreshold' tag: {threshold}")
    except:
        logger.info(f"Set threshold of {metric} with default value: {threshold}")
    return threshold

def createUnHealthyHostCountAlarm(tg, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    lbName = '/'.join(tg["LoadBalancerArn"].split(':')[5].split('/')[1:])
    tgName = tg["TargetGroupName"]
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
                                'Value': f'targetgroup/{tgName}'
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
        Threshold=getThreshold(tg.get('Tags', []), 'UnHealthyHostCount', 1),
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
    lbName = '/'.join(tg["LoadBalancerArn"].split(':')[5].split('/')[1:])
    tgName = tg["TargetGroupName"]
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
        Threshold=getThreshold(tg.get('Tags', []), 'TargetResponseTime', 0.1),
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
    lbName = '/'.join(lb["Name"].split(':')[5].split('/')[1:])
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
        Threshold=getThreshold(lb.get('Tags', []), 'Target5XXRate', 1),
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
    logger.debug(f'Response of describe_target_groups: {page_iterator}')
    targetGroups = []
    for page in page_iterator:
        for tg in page["TargetGroups"]:
            if tg["LoadBalancerArns"] and tg["LoadBalancerArns"][0].split("/")[1]=='app':
                targetGroups.append({
                    "LoadBalancerArn": tg["LoadBalancerArns"][0], 
                    "TargetGroupName": tg["TargetGroupName"],
                    "TargetGroupArn": tg["TargetGroupArn"]
                })
    
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    paginator = client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/ALB-')
    logger.debug(f'Response of describe_alarms: {page_iterator}')
    alarmNames = []
    for page in page_iterator:
        alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))

    # 获取TargetGroup标签
    targetGroupTag = {}
    client = boto3.client('elbv2') 
    for i in range(0,len(targetGroups), 20):
        response = client.describe_tags(ResourceArns=list(map(lambda x:x.get("TargetGroupArn"), targetGroups[i:i+20])))
        targetGroupTag.update(dict(zip(map(lambda x:x["ResourceArn"], response.get("TagDescriptions")), map(lambda x:x.get('Tags', []), response.get("TagDescriptions")))))
    logger.debug(f'targetGroupTag: {targetGroupTag}')
    # 创建TargetGroup告警
    numOfAlarmsCreated = 0
    for tg in targetGroups:
        tg['Tags'] = targetGroupTag[tg["TargetGroupArn"]]
        alarmName, created = createUnHealthyHostCountAlarm(tg, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
        alarmName, created = createTargetResponseTimeAlarm(tg, alarmNames)
        numOfAlarmsCreated += 1 if created else 0
    # 获取LoadBalancer标签
    loadBalancers = list(set(map(lambda x:x["LoadBalancerArn"], targetGroups))) 
    loadBalancerTag = {}
    client = boto3.client('elbv2') 
    for i in range(0,len(loadBalancers), 20):
        response = client.describe_tags(ResourceArns=loadBalancers[i:i+20])
        loadBalancerTag.update(dict(zip(map(lambda x:x["ResourceArn"], response.get("TagDescriptions")), map(lambda x:x.get('Tags', []), response.get("TagDescriptions")))))
    logger.debug(f'loadBalancerTag: {targetGroupTag}')
    # 创建LoadBalancer告警      
    for lbName in loadBalancers:
        lb = {
            "Name": lbName,
            "Tags": loadBalancerTag[lbName]
        }
        alarmName, created = createHTTPCode_Target_5XX_RateAlarm(lb, alarmNames)
        numOfAlarmsCreated += 1 if created else 0
            
    # 删除不再使用的告警
    logger.info(f'Delete orphan alarms: {alarmNames}')
    client = boto3.client('cloudwatch')
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


