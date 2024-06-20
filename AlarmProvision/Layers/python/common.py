import os
import json
import yaml
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)

def getThreshold(tags, metric, default):
    threshold = default
    try:
        thresholdJson = list(filter(lambda x:x.get("Key")=='AlarmThreshold', tags))[0].get("Value") if type(tags)==list else tags.get('AlarmThreshold')
        if thresholdJson=='disable':
            return None
        else:
            threshold = json.loads(thresholdJson)[metric]
        logger.info(f"Set threshold of {metric} according 'AlarmThreshold' tag: {threshold}")
    except:
        logger.info(f"Set threshold of {metric} with default value: {threshold}")
    return threshold
    
def getSSMActions(account_id, region, alarmdef):
    alarm_actions = []
    ok_actions = []
    if os.getenv('SNSTopicArn'):
        alarm_actions.append(os.getenv('SNSTopicArn'))
        ok_actions.append(os.getenv('SNSTopicArn'))
    response_plan = alarmdef.get('ResponsePlanName')
    opsitem_sev = alarmdef.get("OpsItemSev")
    if response_plan:
        # arn:aws:ssm-incidents::account-id:response-plan/response-plan-name
        alarm_actions.append(f'arn:aws:ssm-incidents::{account_id}:response-plan/{response_plan}')
    elif opsitem_sev:
        # arn:aws:ssm:region:account-id:opsitem:severity#CATEGORY=category-name
        opsitemarn = f'arn:aws:ssm:{region}:{account_id}:opsitem:{opsitem_sev}'
        opsitemarn += f'#CATEGORY={alarmdef.get("OpsItemCategory")}' if alarmdef.get("OpsItemCategory") else ''
        alarm_actions.append(opsitemarn)   
    return alarm_actions, ok_actions
    
def getInstanceTypes(): 
    # 获取所有EC2实例类型
    client = boto3.client('ec2')
    paginator = client.get_paginator('describe_instance_types')
    page_iterator = paginator.paginate()
    result = {}
    for page in page_iterator:
        for r in page["InstanceTypes"]:
            result[r["InstanceType"]] = r
    return result



