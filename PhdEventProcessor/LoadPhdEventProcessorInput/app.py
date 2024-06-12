import os
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    service = event["detail"]["service"]
    eventTypeCode = event["detail"]["eventTypeCode"]
    eventTypeCategory = event["detail"]["eventTypeCategory"]
    beijing_time = datetime.datetime.strptime(event["detail"]["startTime"][:25].strip(), '%a, %d %b %Y %H:%M:%S').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    eventDescription = event["detail"].get("eventDescription")
    affectedEntities = event["detail"].get("affectedEntities")
    return {
        'account': event['account'],
        'region': event['region'],
        'service': service, 
        'eventTypeCode': eventTypeCode, 
        'eventTypeCategory': eventTypeCategory, 
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'eventDescription': eventDescription, 
        'affectedEntities': affectedEntities
    }
