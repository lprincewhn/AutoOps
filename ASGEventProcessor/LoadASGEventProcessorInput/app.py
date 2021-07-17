import os
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    beijing_time = datetime.datetime.strptime(event["detail"]["StartTime"][:25].strip(), '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    eventType = event['detail-type']
    asgName = event['detail']['AutoScalingGroupName']
    instanceId = event['detail']['EC2InstanceId']
    cause = event['detail']['Cause']
    return {
        'account': event['account'],
        'region': event['region'],
        'eventType': eventType, 
        'asgName': asgName, 
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'instanceId': instanceId, 
        'cause': cause
    }
