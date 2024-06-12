import json
import string
import datetime

def lambda_handler(event, context):
    print(f'Event In: {json.dumps(event)}')
    resources = event.get('resources')
    daysToExpiry = event.get('detail').get('DaysToExpiry')
    return {'resources': resources, 'daysToExpiry': daysToExpiry}
