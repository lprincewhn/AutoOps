import os
import json
import datetime
import logging


logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    newEvaluationResult = event["detail"]["newEvaluationResult"]
    configRuleName = event["detail"]["configRuleName"]
    beijing_time = datetime.datetime.strptime(newEvaluationResult["resultRecordedTime"][:19], '%Y-%m-%dT%H:%M:%S').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    annotation = newEvaluationResult.get("annotation")
    event = {
        'account': event['account'],
        'region': event['region'],
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'resourceType': event['detail']['resourceType'], 
        'resourceId': event['detail']['resourceId'],
        'configRuleName': configRuleName,
        'annotation': annotation
    }
    logger.info(f'Event Out: {event}')
    return event

