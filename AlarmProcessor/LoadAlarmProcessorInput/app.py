import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["detail"]["alarmName"]
    beijing_time = datetime.datetime.strptime(event["time"], '%Y-%m-%dT%H:%M:%SZ').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    metrics = event["detail"]["configuration"]["metrics"]
    currentState = event["detail"]["state"]["value"]
    previousState = event["detail"]["previousState"]["value"]
    reason = event["detail"]["state"]["reason"]
    reasonData = event["detail"]["state"].get("reasonData")
    recentDatapoints = json.loads(reasonData)["recentDatapoints"] if reasonData else ''
    print(f'ReasonData: {reasonData}')
    eventOut = {
        'account': event['account'],
        'region': event['region'],
        'resources': event['resources'],
        'alarmName': alarmName, 
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'service': alarmName.split('-')[0], 
        'metrics': metrics, 
        'currentState': currentState,
        'previousState': previousState, 
        'reason': reason,
        'eventData': json.dumps(event)
    }
    recentDatapoints = json.loads(reasonData)["recentDatapoints"] if reasonData else [] 
    if recentDatapoints:
        eventOut['alarmValue'] = recentDatapoints[0]
    return eventOut
