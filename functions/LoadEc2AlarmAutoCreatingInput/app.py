import string
import datetime

def lambda_handler(event, context):
    print(f'Input: {event}')
    instancdId = event.get('detail').get('instance-id')
    state = event.get('detail').get('state')
    return {'InstanceId': instancdId, 'State': state}
