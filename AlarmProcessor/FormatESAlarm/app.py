import json
import boto3
import datetime
import time

    
def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["alarmName"]
    timestamp = event["timestamp"]
    alarmValue = event["alarmValue"]
    esdomain_name = event["metrics"][0]["metricStat"]["metric"]["dimensions"]["DomainName"]
    message = None
    if 'ClusterStatus.red-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} 状态变为红色：存在一到多个主分片其及副本无法分配给节点。'
    if 'ClusterStatus.yellow-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} 状态变为黄色：存在一到多个副本无法分配给节点。'
    if 'Low-FreeStorageSpace-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} 可用存储空间不足: {event["reason"]}'
    if 'ClusterIndexWritesBlocked-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} 无法写入请求。'
    if 'Low-Nodes-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} 健康节点数不足：当前仅有{alarmValue}个监控节点。'
    if 'AutomatedSnapshotFailure-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} 自动快照失败。'
    if 'CPUUtilization-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} CPU利用率达{alarmValue}%: {event["reason"]}'
    if 'JVMMemoryPressure-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} JVM内存利用率达{alarmValue}%: {event["reason"]}'
    if 'KMSKeyError-Alarm' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} 的KMS加密密钥已禁用。重新启用它可恢复正常操作。'
    if 'KMSKeyInaccessible' in alarmName:
        message = f'{timestamp},  AWS ElasticSearch 集群 {esdomain_name} 的KMS加密密钥已被删除或已撤销其对Amazon ES的授权。您无法恢复处于此状态的域，但如果您有一个手动快照，则可以用它来迁移至新的域。'
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】ElasticSearch告警'
    print(f'Event Out: {event}')
    return event

