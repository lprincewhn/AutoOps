import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('cloudfront')
    if not event.get('DistributionOwner'):
        print('Tag "Owner" does not exist. Tag it with user name or role name.')
        response = client.tag_resource(
            Resource=event['DistributionArn'],
            Tags={
                'Items': [
                    {
                        'Key': 'Owner',
                        'Value': event['IdentityName']
                    }
                ]
            }
        )
        print(f'Response: {response}')
    if (not event.get('DistributionProject')) and event.get('IdentityProject'):
        print(event.get('IdentityName') + " has Project Tag of " + event.get('IdentityProject'))
        print("Distribution has no Tag 'Project'. Tag it with user's project tag.")
        response = client.tag_resource(
            Resource=event['DistributionArn'],
            Tags={
                'Items': [
                    {
                        'Key': 'Project',
                        'Value': event['IdentityProject']
                    }
                ]
            }
        )
        print(f'Response: {response}')
    return event
