import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

volumes_without_tag = {}

def getVolumesWithoutTag(tagKey):
    global volumes_without_tag
    if volumes_without_tag.get(tagKey):
        return volumes_without_tag.get(tagKey)
    client = boto3.client('resourcegroupstaggingapi')
    paginator = client.get_paginator('get_resources')
    page_iterator = paginator.paginate(
        TagFilters=[{"Key":tagKey}],
        ResourceTypeFilters=['ec2:volume']
    )
    volumesHasTag = []
    arnPrefix = None
    for page in page_iterator:
        for r in page["ResourceTagMappingList"]:
            volumesHasTag.append(r.get("ResourceARN").split('/')[1])
            arnPrefix = r.get("ResourceARN").split('/')[0] + '/'
    volumes_without_tag[tagKey] = (volumesHasTag, arnPrefix)
    return volumes_without_tag.get(tagKey)

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    logging.info(f'Environment TAGS_TO_SYNC: {os.getenv("TAGS_TO_SYNC")}')
    if not os.getenv("TAGS_TO_SYNC"):
        logging.info(f'No environment TAGS_TO_SYNC found. Please set it to specify what tags need to be copied.') 
        return event   
    tags_to_sync = list(map(lambda x:x.strip(), os.getenv('TAGS_TO_SYNC').split(',')))
    logging.info(f'TAGS_TO_SYNC: {tags_to_sync}')    
    # 获取所有EC2实例
    client = boto3.client('ec2')
    paginator = client.get_paginator('describe_instances')
    page_iterator = paginator.paginate()
    instanceList = []
    for page in page_iterator:
        for r in page["Reservations"]:
            for i in r["Instances"]:
                instanceList.append(i)

    for i in instanceList:
        tags_on_ec2 = i.get('Tags', [])
        logging.info(f'Tags on {i.get("InstanceId")}: {tags_on_ec2}')
        tags = list(filter(lambda x:x.get('Key') in tags_to_sync, tags_on_ec2))
        logging.info(f'Tags to be copied to EBS Volumes: {tags}')
        for t in tags:
            # 获取已经没有打标签的EBS卷
            volumesHasTag, arnPrefix = getVolumesWithoutTag(t.get("Key"))           
            # 获取实例上挂载的EBS卷
            volumeOfEc2 = list(map(lambda m: m['Ebs']['VolumeId'], filter(lambda m: m.get('Ebs'), i['BlockDeviceMappings'])))
            # 给实例上挂载的但没有标签的EBS卷打默认标签
            volumeArns = list(map(lambda m: arnPrefix+m,filter(lambda x: not x in volumesHasTag, volumeOfEc2)))
            if volumeArns:
                client = boto3.client('resourcegroupstaggingapi')
                response = client.tag_resources(
                    ResourceARNList=volumeArns,
                    Tags={t.get("Key"): t.get("Value")}
                )
                logging.debug(f'Response: {response}')
                logging.info(f'Created Tag: {t}, on volumes: {volumeArns}')
                event['CreatedTags'] = event.get('CreatedTags', []) + [{"Tag": t, "volumeArns": volumeArns}]
    logging.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})
