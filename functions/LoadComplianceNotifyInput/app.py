import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    newEvaluationResult = event["detail"]["newEvaluationResult"]
    beijing_time = datetime.datetime.strptime(newEvaluationResult["resultRecordedTime"][:19], '%Y-%m-%dT%H:%M:%S').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    annotation = newEvaluationResult.get("annotation")
    event = {
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'resourceType': event['detail']['resourceType'], 
        'resourceId': event['detail']['resourceId']
    }
    if annotation:
        event["message"] = annotation
        event["subject"] = "IAM用户不合规"
    print(f'Event Out: {event}')
    return event

