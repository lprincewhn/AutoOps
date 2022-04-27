import os
import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    distributionId = None
    eventId = event.get('detail').get('EventID')
    operation = None
    if eventId == 'RDS-EVENT-0005':
        operation = 'created'
        dbInstanceIdentifier = event.get('detail').get('SourceIdentifier').split(':')[-1] 
    if eventId == 'RDS-EVENT-0043':
        operation = 'restored'
        dbInstanceIdentifier = event.get('detail').get('SourceIdentifier').split(':')[-1]
    if eventId == 'RDS-EVENT-0003':
        operation = 'deleted'
        dbInstanceIdentifier = event.get('detail').get('SourceIdentifier').split(':')[-1]
    if eventId == 'RDS-EVENT-0017':
        operation = 'storage_changed'
        dbInstanceIdentifier = event.get('detail').get('SourceIdentifier').split(':')[-1]
    return {'dbInstanceIdentifier': dbInstanceIdentifier, 'operation': operation}
