import os
import json
import boto3
import logging
import datetime

logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event, default=str)}')
    events = []
    for event in event['Records']:
        message = json.loads(event["Sns"]["Message"])
        eventtime = datetime.datetime.strptime(event["Sns"]["Timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
        detail_type = resounce_name = ""
        for k,v in message.items():
            if k.startswith('ElastiCache:'):
                detail_type = k
                resounce_name = v
                
        eventbridge = boto3.client('events')
        events.append({
            'Source':'AutoOpsElastiCacheEvent',
            'DetailType': detail_type,
            'Resources': [resounce_name],
            'Detail': json.dumps(message, sort_keys=True, default=str),
            'EventBusName': os.getenv('EventBusName')
        })
    response = eventbridge.put_events(
        Entries=events,
    )
    return len(events)
        
if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    payload = json.load(open("./examples/SnapshotComplete.json"))
    lambda_handler(payload, None)
    
    