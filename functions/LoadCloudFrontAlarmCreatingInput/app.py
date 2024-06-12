import string
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    distributionId = None
    eventName = event.get('detail').get('eventName')
    operation = None
    if eventName.startswith('Create'):
        operation = 'created'
        distributionId = event.get('detail').get('responseElements').get('distribution').get('id')
    if eventName.startswith('Delete'):
        operation = 'deleted'
        distributionId = event.get('detail').get('requestParameters').get('id')
    return {'distributionId': distributionId, 'operation': operation}
