import os
import re
import boto3
import json
import datetime
import requests
import base64
import logging

logging.basicConfig()
logger = logging.getLogger("LambdaInvocationCheck")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def getLambdaInvocations(region):
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    queries = [
        {
            'Id': 'invocations',
            'Label': 'invocations',
            'Expression': "SUM(SEARCH(' {AWS/Lambda,FunctionName} MetricName=\"Invocations\" AND us-east-1 ', 'Sum', 60))",
            'ReturnData': True 
        }
    ]
    response = cloudwatch.get_metric_data(
        MetricDataQueries=queries,
        StartTime=datetime.datetime.utcnow() - datetime.timedelta(hours=3),
        EndTime=datetime.datetime.utcnow(),
        ScanBy='TimestampDescending',
        MaxDatapoints=12000
    )
    return response

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}...')
    region_list = ['us-east-1','us-east-2','us-west-1','us-west-2','eu-west-1','eu-central-1','eu-west-2','ap-south-1','ap-southeast-1','ap-northeast-1','ap-northeast-2','ap-southeast-2','sa-east-1'] 
    eventOut = {}
    message = ""
    customer = os.getenv('CUSTOMER_DATA1')
    for r in region_list:
        response = getLambdaInvocations(r)
        max_invocations = max(response['MetricDataResults'][0]['Values']) if response['MetricDataResults'][0]['Values'] else 0
        logger.debug(response['MetricDataResults'][0]['Values'])
        quota = int(os.getenv(f'RPS_QUOTA_{r.replace("-", "_")}', '10000'))
        estimated_rps = int(max_invocations/60*5)
        threshold = quota * 0.5
        logger.info(f'区域: {r}, 配额: {quota}/s, 阈值: {threshold}/s, 过去3个小时最大峰值: {estimated_rps}/s({max_invocations}/60*5); ')
        if estimated_rps > quota:
            message += f'区域: {r}, 配额: {quota}/s, 阈值: {threshold}/s, 过去3个小时最大峰值: {estimated_rps}/s; '
        eventOut[r] = max_invocations 
    if message:
        message = f'【AWS】 lambda-threshold 【AWS-CDN+】[{customer}-客户告警]，Lambda@Edge调用次数超出阈值。详情如下: ' + message
        eventOut['message'] = message
        eventOut['receiver'] = 'all'
    logger.info(f'Event Out: {json.dumps(eventOut)}...')
    return eventOut
            
if __name__ == '__main__':
    lambda_handler({}, None)
