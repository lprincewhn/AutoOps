import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    eventOut = {
        "message": json.dumps(event, indent=2),
        "subject": event["detail-type"]
    }
    print(f'Event Out: {eventOut}')
    return eventOut

