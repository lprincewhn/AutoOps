import os
import json
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    event['subject'] = 'AWS告警检查和修复情况'
    event['receiver'] = os.getenv('Receiver', 'all')
    alarmsDeletedStr = "\n".join(event["alarmsDeleted"])
    event['message'] = f'创建告警{event["numOfAlarmsCreated"]}条;\n删除告警{len(event["alarmsDeleted"])}条: \n{alarmsDeletedStr}'

    if event['message']:
        logger.info(f'SNSTopicArn: {os.getenv("SNSTopicArn")}')
        topicArn = os.getenv("SNSTopicArn")
        topicRegion = topicArn.split(':')[3]
        client = boto3.client('sns',region_name=topicRegion)
        response = client.publish(
            TopicArn=os.getenv('SNSTopicArn'),
            Subject=event.get('subject'),
            MessageAttributes= {'receiver':  {'DataType': 'String', 'StringValue': event.get('receiver', 'all')}},
            Message=event.get('message')
        )
        event['snsResponse'] = response
        logger.info(f'Event Out: {json.dumps(event)}')
    return event
