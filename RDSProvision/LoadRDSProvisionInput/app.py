import string
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    distributionId = None
    eventCategories = event.get('detail').get('EventCategories')
    operation = None
    if 'creation' in eventCategories:
        operation = 'created'
        dbInstanceIdentifier = event.get('detail').get('SourceIdentifier').split(':')[-1]
    if 'deletion' in eventCategories:
        operation = 'deleted'
        dbInstanceIdentifier = event.get('detail').get('SourceIdentifier').split(':')[-1]
    return {'dbInstanceIdentifier': dbInstanceIdentifier, 'operation': operation}
