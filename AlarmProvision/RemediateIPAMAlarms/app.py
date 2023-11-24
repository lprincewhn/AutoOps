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

def createSubnetIPUsageAlarm(cidr, alarmNames):
    sns_topic = os.getenv('SNSTopicArn')
    actions_enable = (sns_topic!=None) 
    actions = [sns_topic] if sns_topic else []
    client = boto3.client('cloudwatch')
    alarmName = f'AWS/IPAM-SubnetIPUsage-{cidr["ResourceRegion"]}-{cidr["ResourceId"]}'
    if alarmName in alarmNames:
        alarmNames.remove(alarmName)
        return alarmName, False
    addressCount = 2**(32-int(cidr["ResourceCidr"].split('/')[1]))
    addressThreshold = 20
    addressPercentageThreshold = 1
    threshold = min(100-addressPercentageThreshold, (addressCount-addressThreshold)*100/addressCount)
    response = client.put_metric_alarm(
        AlarmName=alarmName,
        AlarmDescription=f'子网剩余IP数量不足{addressThreshold}个或{addressPercentageThreshold}%',
        ActionsEnabled=actions_enable,
        AlarmActions=actions,
        OKActions=actions,
        Metrics=[
            {
                'Id': 'm1',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/IPAM',
                        'MetricName': 'SubnetIPUsage',
                        'Dimensions': [
                            {
                                'Name': 'SubnetID',
                                'Value': cidr["ResourceId"]
                            },
                            {
                                'Name': 'OwnerID',
                                'Value': cidr["ResourceOwnerId"]
                            },
                            {
                                'Name': 'VpcID',
                                'Value': cidr["VpcId"]
                            },
                            {
                                'Name': 'Region',
                                'Value': cidr["ResourceRegion"]
                            },
                            {
                                'Name': 'ScopeID',
                                'Value': cidr["IpamScopeId"]
                            },
                            {
                                'Name': 'AddressFamily',
                                'Value': 'IPv4'
                            },
                        ]
                    },
                    'Period': 86400,
                    'Stat': 'Average',
                },
                'Label': cidr["ResourceCidr"],
                'ReturnData': True,
            },
        ],
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=threshold,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='breaching',
        Tags=[]
    )
    return alarmName, True

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    # 获取所有IPAM中的子网资源
    client = boto3.client('ec2')
    paginator = client.get_paginator('describe_ipam_scopes')
    page_iterator = paginator.paginate()
    logger.debug(f'Response of describe_ipam_scopes: {page_iterator}')
    resourceCidrs = []
    for page in page_iterator:
        for s in page["IpamScopes"]:
            if s["IpamScopeType"]=='private':
                paginator = client.get_paginator('get_ipam_resource_cidrs')
                page_iterator1 = paginator.paginate(IpamScopeId=s["IpamScopeId"])
                logger.debug(f'Response of get_ipam_resource_cidrs: {page_iterator1}')
                for page1 in page_iterator1:
                    for c in page1["IpamResourceCidrs"]:
                        resourceCidrs.append(c)
    # 获取已创建的告警
    client = boto3.client('cloudwatch')
    paginator = client.get_paginator('describe_alarms')
    page_iterator = paginator.paginate(AlarmNamePrefix=f'AWS/IPAM-')
    alarmNames = []
    for page in page_iterator:
        alarmNames += list(map(lambda x:x.get('AlarmName'), page['MetricAlarms']))

    # 创建告警
    numOfAlarmsCreated = 0
    for cidr in resourceCidrs:
        if cidr["ResourceType"]=='subnet':
            alarmName, created = createSubnetIPUsageAlarm(cidr, alarmNames)
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



