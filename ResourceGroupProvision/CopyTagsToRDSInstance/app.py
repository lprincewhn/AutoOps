import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

instances_without_tag = {}

def getRDSInstancesWithoutTag(tagKey):
    global instances_without_tag
    if instances_without_tag.get(tagKey):
        return instances_without_tag.get(tagKey)
    client = boto3.client('resourcegroupstaggingapi')
    paginator = client.get_paginator('get_resources')
    page_iterator = paginator.paginate(
        TagFilters=[{"Key":tagKey}],
        ResourceTypeFilters=['rds:db']
    )
    instancesHasTag = []
    arnPrefix = None
    for page in page_iterator:
        for r in page["ResourceTagMappingList"]:
            print(r.get("ResourceARN"))
            instancesHasTag.append(r.get("ResourceARN").split(':')[6])
            arnPrefix = ":".join(r.get("ResourceARN").split(':')[:-1]) + ':'
    instances_without_tag[tagKey] = (instancesHasTag, arnPrefix)
    return instances_without_tag.get(tagKey)

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    logging.info(f'Environment TAGS_TO_SYNC: {os.getenv("TAGS_TO_SYNC")}')
    if not os.getenv("TAGS_TO_SYNC"):
        logging.info(f'No environment TAGS_TO_SYNC found. Please set it to specify what tags need to be copied.')
        return event
    tags_to_sync = list(map(lambda x:x.strip(), os.getenv('TAGS_TO_SYNC').split(',')))
    logging.info(f'TAGS_TO_SYNC: {tags_to_sync}')    
    # 获取所有EC2实例
    client = boto3.client('rds')
    paginator = client.get_paginator('describe_db_clusters')
    page_iterator = paginator.paginate()
    clusterList = []
    for page in page_iterator:
        for c in page["DBClusters"]:
            clusterList.append(c)

    for c in clusterList:
        tags_on_cluster = c.get('TagList', [])
        logging.info(f'Tags on {c.get("DBClusterIdentifier")}: {tags_on_cluster}')
        tags = list(filter(lambda x:x.get('Key') in tags_to_sync, tags_on_cluster))
        logging.info(f'Tags to be copied to RDS Instances: {tags}')
        for t in tags:
            # 获取已经没有打标签的RDS数据库实例
            instancesHasTag, arnPrefix = getRDSInstancesWithoutTag(t.get("Key"))           
            # 获取集群的实例成员
            clusterMembers = list(map(lambda m: m['DBInstanceIdentifier'], filter(lambda m: m.get('DBInstanceIdentifier'), c['DBClusterMembers'])))
            # 给没有标签的实例成员打默认标签
            dbArns = list(map(lambda m: arnPrefix+m,filter(lambda x: not x in instancesHasTag, clusterMembers)))
            if dbArns:
                client = boto3.client('resourcegroupstaggingapi')
                response = client.tag_resources(
                    ResourceARNList=dbArns,
                    Tags={t.get("Key"): t.get("Value")}
                )
                logging.debug(f'Response: {response}')
                logging.info(f'Created Tag: {t}, on db instances: {dbArns}')
                event['CreatedTags'] = event.get('CreatedTags', []) + [{"Tag": t, "dbArns": dbArns}]

    logging.info(f'Event Out: {json.dumps(event)}')
    return event

if __name__ == '__main__':
    lambda_handler({}, {})
