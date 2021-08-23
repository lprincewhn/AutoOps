import os
import boto3

def lambda_handler(event, context):
    print(f'Event In: {event}')
    client = boto3.client('rds')
    dbInstanceIdentifier = event["dbInstanceIdentifier"]
    response = client.describe_db_instances(
        DBInstanceIdentifier=dbInstanceIdentifier
    )
    print(f'Response: {response}')
    event["storage_type"] = response['DBInstances'][0].get('StorageType')
    event["storage_size"] = response['DBInstances'][0].get('AllocatedStorage')
    event["iops"] = response['DBInstances'][0].get('Iops')
    print(f'Event Out: {event}')
    return event
