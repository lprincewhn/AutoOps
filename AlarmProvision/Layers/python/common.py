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



