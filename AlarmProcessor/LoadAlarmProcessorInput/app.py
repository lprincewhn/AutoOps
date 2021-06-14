import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["detail"]["alarmName"]
    beijing_time = datetime.datetime.strptime(event["time"], '%Y-%m-%dT%H:%M:%SZ').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    metrics = event["detail"]["configuration"]["metrics"]
    reason = event["detail"]["state"]["reason"]
    reasonData = json.loads(event["detail"]["state"]["reasonData"])
    print(f'ReasonData: {reasonData}')
    return {
        'alarmName': alarmName, 
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'service': alarmName.split('-')[0], 
        'metrics': metrics, 
        'reason': reason,
        'alarmValue': reasonData["recentDatapoints"][0]
    }
