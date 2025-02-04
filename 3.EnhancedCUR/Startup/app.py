import os
import json
import boto3
import logging
import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    input_para = (datetime.datetime.utcnow().replace(day=1) - datetime.timedelta(days=2)).strftime("%Y-%m")
    try:
        input_para = f'{event["year"]}-{event["month"]}'
    except:
        pass
    logger.info(f'Start {os.getenv("EnhanceCURStateMachineArn")} of month {input_para}')
    client = boto3.client('stepfunctions')
    response = client.start_execution(
        stateMachineArn=os.getenv("EnhanceCURStateMachineArn"),
        input=json.dumps({"time": input_para})
    )
    return response["executionArn"]

if __name__ == '__main__':
    lambda_handler({}, {})


