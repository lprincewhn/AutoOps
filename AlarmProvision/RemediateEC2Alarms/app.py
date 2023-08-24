import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

def createCPUUtilizationAlarm(instanceId, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    alarmName = f'AWS/EC2-CPUUtilization-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
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
        Threshold=80,
        ComparisonOperator='GreaterThanThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def createStatusCheckFailed_SystemAlarm(instanceId, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    region = os.getenv('AWS_REGION')
    actions_enable = (sns_topic!=None) 
    actions = [f'arn:aws:automate:{region}:ec2:recover', sns_topic] if sns_topic else [f'arn:aws:automate:{region}:ec2:recover']
    client = boto3.client('cloudwatch')
    alarmName = f'AWS/EC2-StatusCheckFailed_System-{instanceId}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    response = client.put_metric_alarm(
        AlarmName=alarmName,
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
    logging.debug(f'Response of put_metric_alarm: {response}')
    return alarmName, True

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    # 获取所有EC2实例
    client = boto3.client('ec2')
    response = client.describe_instances()
    logging.debug(f'Response of describe_instances: {response}')
    instanceIds = []
    for r in response["Reservations"]:
        for i in r["Instances"]:
            instanceIds.append(i["InstanceId"])
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    response = client.describe_alarms(
        AlarmNamePrefix=f'AWS/EC2-'
    )
    logging.debug(f'Response of describe_alarms: {response}')
    alarmNames = list(map(lambda x:x.get('AlarmName'), response['MetricAlarms']))
    # 创建告警
    numOfAlarmsCreated = 0
    for i in instanceIds:
        alarmName, created = createCPUUtilizationAlarm(i, alarmNames)
        numOfAlarmsCreated += 1 if created else 0 
        try:
            alarmName, created = createStatusCheckFailed_SystemAlarm(i, alarmNames)
            numOfAlarmsCreated += 1 if created else 0 
        except:
            pass
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


