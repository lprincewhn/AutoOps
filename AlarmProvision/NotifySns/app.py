import os
import json
import boto3
import logging
logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    event['subject'] = 'AWS告警检查和修复情况'
    event['receiver'] = os.getenv('Receiver', 'all')
    alarmsDeletedStr = "\n".join(event["alarmsDeleted"])
    event['message'] = f'创建告警{event["numOfAlarmsCreated"]}条;\n删除告警{len(event["alarmsDeleted"])}条: \n{alarmsDeletedStr}'

    if event['message']:
        logging.info(f'SNSTopicArn: {os.getenv("SNSTopicArn")}')
        topicArn = os.getenv("SNSTopicArn")
        topicRegion = topicArn.split(':')[3]
        client = boto3.client('sns',region_name=topicRegion)
        response = client.publish(
            TopicArn=os.getenv('SNSTopicArn'),
            Subject=event.get('subject'),
            MessageAttributes= {'receiver':  {'DataType': 'String', 'StringValue': event.get('receiver', 'all')}},
            Message=event.get('message')
        )
        logging.debug(f'Response of publish: {response}')
        event['snsResponse'] = response
        logging.info(f'Event Out: {json.dumps(event)}')
    return event
