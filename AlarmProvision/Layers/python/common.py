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
        threshold = json.loads(thresholds[0].get("Value"))[metric]
        logger.info(f"Set threshold of {metric} according 'AlarmThreshold' tag: {threshold}")
    except:
        logger.info(f"Set threshold of {metric} with default value: {threshold}")
    return threshold
    
def getResponseplan(tags, default):
    responseplans = list(filter(lambda x:x.get("Key")=='AlarmResponsePlan', tags))
    if responseplans:
        logger.info(f"Set dedicate response plan from resource tag")
        return responseplans[0].get("Value")
    if default:
        logger.info(f"Set default response plan from lambda environment")
        return default
    logger.info(f"No response plan set")
    return None

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



