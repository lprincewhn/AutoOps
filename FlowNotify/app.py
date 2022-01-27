import os
import json
import boto3
import logging
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    beijing_time = datetime.datetime.strptime(event["time"], '%Y-%m-%dT%H:%M:%SZ').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    eventOut = {
        'account': event['account'],
        'region': event['region'],
        'resources': event['resources'],
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'executionArn': event['detail']['executionArn'],
        'stateMachineArn': event['detail']['stateMachineArn']
    }
    message = json.dumps(eventOut, indent=2)
    message += f'\n\n通过以下链接查看执行详情: https://console.aws.amazon.com/states/home?region={event["region"]}#/executions/details/{eventOut["executionArn"]}'
    print(message)
    subject = '【AWS通知】StepFunction执行失败'
    receiver = 'ops-admin'
    print(f'SNSTopicArn: {os.getenv("SNSTopicArn")}')
    topicArn = os.getenv("SNSTopicArn")
    topicRegion = topicArn.split(':')[3]
    client = boto3.client('sns',region_name=topicRegion)
    response = client.publish(
        TopicArn=os.getenv('SNSTopicArn'),
        Subject=subject,
        Message=message,
        MessageAttributes= {"receiver":  {"DataType": "String", "StringValue": event.get("receiver", "ops-admin")}}
    )
    print(response)
    return response 
