import os
import logging


logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    account = event['account']
    region = event['region']
    timestamp = event["timestamp"]
    message = None
    if 'IamUserConfigRule' in event['configRuleName']:
        message = f'''时间: {timestamp}
AWS帐号：{account}
AWS区域：{region}
资源类型：IAM用户
事件：{event["annotation"]}
详情：{event["annotation"]} 点击以下链接查看不合规资源：https://console.aws.amazon.com/config/home?region={event["region"]}#/rules/details?configRuleName={event["configRuleName"]}
'''
    if message:
        event["message"] = message
        event["subject"] = '【AWS通知】IAM合规性事件通知'
        event['receiver'] = os.getenv('RECEIVER', 'all')
    logger.info(f'Event Out: {event}')
    return event

