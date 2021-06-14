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
    requests, last_requests, llast_requests, error_rate, cache_hit_rate, bytes_downloaded = get_metrics(distribution_id)
    event['requests'] = requests
    event['last_requests'] = last_requests
    event['llast_requests'] = llast_requests
    event['error_rate'] = error_rate
    event['cache_hit_rate'] = cache_hit_rate
    event['bytes_downloaded'] = bytes_downloaded
    if llast_requests>20000 and 'Low-RequestsChangeRate-Alarm' in alarmName:
        message = f'{timestamp},  AWS域名 {distribution_name} 请求次数突降, 当前{last_requests}次，为上一周期的{int(last_requests*100/llast_requests)}%。'
    if last_requests>20000 and 'ErrorRate-Alarm' in alarmName:
        message = f'{timestamp},  AWS域名 {distribution_name} 出现异常状态码5xx, 共{int(requests*error_rate/100)}次，占比{error_rate}%。'
    if 'Requests-Alarm' in alarmName:
        message = f'{timestamp},  AWS域名 {distribution_name} 请求数超出阈值, 共{int(requests)}次。'
    if 'OriginBandwidth-Alarm' in alarmName:
        message = f'{timestamp},  AWS域名 {distribution_name} 回源带宽超出阈值, 为{int(bytes_downloaded*(100-cache_hit_rate)*8/300/100/1000/1000)}Mbps。'
    if message: 
        event['message'] = message
        event['subject'] = '【AWS通知】CloudFront告警'
    print(f'Event Out: {event}')
    return event

