import datetime

def lambda_handler(event, context):
    print(f'Input: {event}')
    beijing_time = datetime.datetime.strptime(event["time"], '%Y-%m-%dT%H:%M:%SZ').astimezone(tz =datetime.timezone
    (datetime.timedelta(hours=8))) if event.get("time") else None
    instancdId = event.get('detail').get('instance-id')
    state = event.get('detail').get('state')
    region = event['region']
    eventOut = {
        'account': event.get('account'),
        'region': event.get('region'),
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'InstanceId': instancdId, 
        'State': state
    }

    return eventOut
