import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["detail"]["alarmName"]
    beijing_time = datetime.datetime.strptime(event["time"], '%Y-%m-%dT%H:%M:%SZ').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    metrics = event["detail"]["configuration"]["metrics"]
    reason = event["detail"]["state"]["reason"]
    reasonData = event["detail"]["state"].get("reasonData")
    print(f'ReasonData: {reasonData}')
    return {
        'account': event['account'],
        'region': event['region'],
        'resources': event['resources'],
        'alarmName': alarmName, 
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'service': alarmName.split('-')[0], 
        'metrics': metrics, 
        'reason': reason,
        'alarmValue': json.loads(reasonData)["recentDatapoints"][0] if reasonData else ''
    }
