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
    
def getResponseplan(tags):
    responseplans = list(filter(lambda x:x.get("Key")=='AlarmResponsePlan', tags))
    if responseplans:
        logger.info(f"Set dedicate response plan from resource tag")
        return responseplans[0].get("Value").strip()
    logger.info(f"No response plan set")
    return None
    
def getOpsItem(tags):
    opsitems = list(filter(lambda x:x.get("Key")=='AlarmOpsItem', tags))
    if opsitems:
        logger.info(f"Set dedicate opsitem from resource tag")
        return opsitems[0].get("Value").strip()
    else:   
        logger.info(f"Set default opsitem of 4-Low")
        return "4"
        
def getSSMActions(account_id, region, tags):
    alarm_actions = []
    ok_actions = []
    if os.getenv('SNSTopicArn'):
        alarm_actions.append(os.getenv('SNSTopicArn'))
        ok_actions.append(os.getenv('SNSTopicArn'))
    response_plan = getResponseplan(tags)
    if response_plan:
        # arn:aws:ssm-incidents::account-id:response-plan/response-plan-name
        alarm_actions.append(f'arn:aws:ssm-incidents::{account_id}:response-plan/{response_plan}')
    else:
        opsitem = getOpsItem(tags)
        # arn:aws:ssm:region:account-id:opsitem:severity#CATEGORY=category-name
        alarm_actions.append(f'arn:aws:ssm:{region}:{account_id}:opsitem:{opsitem}')   
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



