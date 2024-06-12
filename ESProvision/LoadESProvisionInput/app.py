import string
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    distributionId = None
    eventName = event.get('detail').get('eventName')
    operation = None
    if eventName.startswith('Create'):
        operation = 'created'
        domainId = event.get('detail').get('responseElements').get('domainStatus').get('domainId')
    if eventName.startswith('Delete'):
        operation = 'deleted'
        domainId = event.get('detail').get('responseElements').get('domainStatus').get('domainId')
    return {'domainId': domainId, 'operation': operation}
