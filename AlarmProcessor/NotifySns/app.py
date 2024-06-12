import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Event In: {event}')
    print(f'SNSTopicArn: {os.getenv("SNSTopicArn")}')
    topicArn = os.getenv("SNSTopicArn")
    topicRegion = topicArn.split(':')[3]
    client = boto3.client('sns',region_name=topicRegion)
    response = client.publish(
        TopicArn=os.getenv('SNSTopicArn'),
        Subject=event.get('subject'),
        Message=event.get('message'),
        MessageAttributes= {"receiver":  {"DataType": "String", "StringValue": event.get("receiver", "all")}}
    )
    print(response)
    return event
