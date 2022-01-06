import os
import json
import boto3
import datetime
import time

def get_distribution_name(distribution):
    cloudfront = boto3.client('cloudfront', region_name='us-east-1')
    response = cloudfront.get_distribution(
        Id=distribution
    )
    print(f'get_distribution_name: {response["Distribution"]}')
    name = response["Distribution"]["DistributionConfig"]["Aliases"]["Items"][0] if response["Distribution"]["DistributionConfig"]["Aliases"]["Quantity"] > 0 else response["Distribution"]["DomainName"]
    return name
    
def get_metrics(distribution):
    cloudwatch = boto3.client('cloudwatch')
    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'requests',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/CloudFront',
                        'MetricName': 'Requests',
                        'Dimensions': [{'Name':'Region','Value':'Global'},{'Name':'DistributionId','Value':distribution}]
                    },
                    'Period': 300,
                    'Stat': 'Sum'
                },
                'Label': 'requests',
                'ReturnData': True
            },
            {
                'Id': 'error_rate',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/CloudFront',
                        'MetricName': '5xxErrorRate',
                        'Dimensions': [{'Name':'Region','Value':'Global'},{'Name':'DistributionId','Value':distribution}]
                    },
                    'Period': 300,
                    'Stat': 'Average'
                },
                'Label': 'error_rate',
                'ReturnData': True
            },
            {
                'Id': 'cache_hit_rate',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/CloudFront',
                        'MetricName': 'CacheHitRate',
                        'Dimensions': [{'Name':'Region','Value':'Global'},{'Name':'DistributionId','Value':distribution}]
                    },
                    'Period': 300,
                    'Stat': 'Average'
                },
                'Label': 'cache_hit_rate',
                'ReturnData': True
            },
            {
                'Id': 'bytes_downloaded',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/CloudFront',
                        'MetricName': 'BytesDownloaded',
                        'Dimensions': [{'Name':'Region','Value':'Global'},{'Name':'DistributionId','Value':distribution}]
                    },
                    'Period': 300,
                    'Stat': 'Sum'
                },
                'Label': 'bytes_downloaded',
                'ReturnData': True
            },
        ],
        StartTime=datetime.datetime.now() - datetime.timedelta(minutes=30),
        EndTime=datetime.datetime.now(),
        ScanBy='TimestampDescending',
        MaxDatapoints=10
    )
    print(f'get_metrics: {response["MetricDataResults"]}')
    requests = int(response["MetricDataResults"][0]["Values"][0]) if len(response["MetricDataResults"][0]["Values"]) > 0 else 0
    last_requests = int(response["MetricDataResults"][0]["Values"][1]) if len(response["MetricDataResults"][0]["Values"]) > 1 else 0
    llast_requests = int(response["MetricDataResults"][0]["Values"][2]) if len(response["MetricDataResults"][0]["Values"]) > 2 else 0
    error_rate = int(response["MetricDataResults"][1]["Values"][0]) if len(response["MetricDataResults"][1]["Values"]) > 0 else 0
    cache_hit_rate = int(response["MetricDataResults"][2]["Values"][0]) if len(response["MetricDataResults"][2]["Values"]) > 0 else 0
    bytes_downloaded = int(response["MetricDataResults"][3]["Values"][0]) if len(response["MetricDataResults"][3]["Values"]) > 0 else 0
    return requests, last_requests, llast_requests, error_rate, cache_hit_rate, bytes_downloaded
    
def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["alarmName"]
    timestamp = event["timestamp"]
    message = None
    distribution_id = alarmName.split('-')[1]
    distribution_name = get_distribution_name(distribution_id)
    customer = os.getenv('CUSTOMER_DATA1')
    if event["currentState"]=="ALARM":
        requests, last_requests, llast_requests, error_rate, cache_hit_rate, bytes_downloaded = get_metrics(distribution_id)
        event['requests'] = requests
        event['last_requests'] = last_requests
        event['llast_requests'] = llast_requests
        event['error_rate'] = error_rate
        event['cache_hit_rate'] = cache_hit_rate
        event['bytes_downloaded'] = bytes_downloaded
        if llast_requests>20000 and 'Low-RequestsChangeRate-Alarm' in alarmName:
            message = f'【AWS】 {distribution_name} 【AWS-CDN+】[{customer}-客户告警]域名：[{distribution_name}]，发生了请求次数突降告警 当前值：域名全网请求数（次）={last_requests}, 为上一周期域名全网请求数的{int(last_requests*100/llast_requests)}%。最近一次告警时间：{timestamp}'
        if last_requests>20000 and 'ErrorRate-Alarm' in alarmName:
            message = f'【AWS】 {distribution_name} 【AWS-CDN+】[{customer}-客户告警]域名：[{distribution_name}]，发生了5xx状态码告警 当前值：域名全网请求数（次）={last_requests},域名全网5xx占比（百分比）={error_rate}%。最近一次告警时间：{timestamp}'
        if 'Requests-Alarm' in alarmName:
            message = f'【AWS】 {distribution_name} 【AWS-CDN+】[{customer}-客户告警]域名：[{distribution_name}]，发生了请求数告警 当前值：域名全网请求数（次）={last_requests}。最近一次告警时间：{timestamp}'
        if 'OriginBandwidth-Alarm' in alarmName:
            message = f'【AWS】 {distribution_name} 【AWS-CDN+】[{customer}-客户告警]域名：[{distribution_name}]，发生了回源带宽告警 当前值：域名全网请求数（次）={last_requests}，域名全网回源带宽（Mbps）={int(bytes_downloaded*(100-cache_hit_rate)*8/300/100/1000/1000)}。最近一次告警时间：{timestamp}'

    if event["currentState"]=="OK" and event["previousState"]=="ALARM":
        requests, last_requests, llast_requests, error_rate, cache_hit_rate, bytes_downloaded = get_metrics(distribution_id)
        event['requests'] = requests
        event['last_requests'] = last_requests
        event['llast_requests'] = llast_requests
        event['error_rate'] = error_rate
        event['cache_hit_rate'] = cache_hit_rate
        event['bytes_downloaded'] = bytes_downloaded
        if 'ErrorRate-Alarm' in alarmName:
            message = f'【AWS】 {distribution_name} 【AWS-CDN+】[{customer}-客户告警]域名：[{distribution_name}]，5xx状态码告警恢复 当前值：域名全网请求数（次）={last_requests},域名全网5xx占比（百分比）={error_rate}%。告警恢复时间：{timestamp}'
        if 'Requests-Alarm' in alarmName:
            message = f'【AWS】 {distribution_name} 【AWS-CDN+】[{customer}-客户告警]域名：[{distribution_name}]，请求数告警恢复 当前值：域名全网请求数（次）={last_requests}。告警恢复时间：{timestamp}'
        if 'OriginBandwidth-Alarm' in alarmName:
            message = f'【AWS】 {distribution_name} 【AWS-CDN+】[{customer}-客户告警]域名：[{distribution_name}]，回源带宽告警恢复 当前值：域名全网请求数（次）={last_requests}，域名全网回源带宽（Mbps）={int(bytes_downloaded*(100-cache_hit_rate)*8/300/100/1000/1000)}。告警恢复时间：{timestamp}'
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】CloudFront告警'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    print(f'Event Out: {event}')
    return event


