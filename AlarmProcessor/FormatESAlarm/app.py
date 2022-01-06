import os
import json
import boto3
import datetime
import time
    
def lambda_handler(event, context):
    print(f'Event In: {event}')
    account = event['account']
    region = event['region']
    alarmName = event["alarmName"]
    currentState = event["currentState"]
    timestamp = event["timestamp"]
    alarmValue = event["alarmValue"]
    esdomain_name = event["metrics"][0]["metricStat"]["metric"]["dimensions"]["DomainName"]
    message = None
    if 'ClusterStatus.red-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：状态变为红色
详情：存在一到多个主分片其及副本无法分配给节点。
'''
    if 'ClusterStatus.yellow-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：状态变为黄色
详情：存在一到多个副本无法分配给节点。
'''
    if 'Low-FreeStorageSpace-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：可用存储空间不足
详情：{event["reason"]}
'''
    if 'ClusterIndexWritesBlocked-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：无法写入请求
'''
    if 'Low-Nodes-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：健康节点数不足
详情：当前仅有{alarmValue}个节点
'''
    if 'AutomatedSnapshotFailure-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：自动快照失败
'''
    if 'CPUUtilization-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：CPU使用率过高
详情：{event["reason"]}
'''
    if 'JVMMemoryPressure-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：JVM内存利用率过高
详情：{event["reason"]}
'''
    if 'KMSKeyError-Alarm' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：KMS加密密钥已禁用
详情：重新启用它可恢复正常操作。
'''
    if 'KMSKeyInaccessible' in alarmName and currentState=='ALARM':
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：ElasticSearch集群
资源名称：{esdomain_name}
事件：KMS加密密钥已被删除或已撤销其对Amazon ES的授权
详情：您无法恢复处于此状态的域，但如果您有一个手动快照，则可以用它来迁移至新的域。
'''
    if message:
        event['message'] = message
        event['subject'] = '【AWS通知】ElasticSearch告警'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    print(f'Event Out: {event}')
    return event

