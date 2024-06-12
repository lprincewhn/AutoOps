import os
import json
import boto3
import logging
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)

time_format = '%Y-%m-%d %H:%M:%S.000000000'

def upload_to_s3(bucket, key, data):
    logger.info(f'Upload data to s3://{bucket}/{key}')
    client = boto3.client('s3', region_name='ap-northeast-1')
    response = client.put_object(
        Body = '\n'.join(map(lambda x: json.dumps(x), data)),
        Bucket = bucket,
        Key = key,
    )
    logger.info(f'Successful to upload to s3://{bucket}/{key}')
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    client = boto3.client('internetmonitor')
    result = []
    response = client.list_internet_events(MaxResults=100)
    refresh_time = datetime.utcnow().strftime(time_format)
    for item in response['InternetEvents']:
        data = {
            'RefreshTime': refresh_time,
            'EventId': item['EventId'],
            'StartedAt': item['StartedAt'].strftime(time_format),
            'ASName': item['ClientLocation']['ASName'],
            'ASNumber': item['ClientLocation']['ASNumber'],
            'Country': item['ClientLocation']['Country'],
            'Subdivision': item['ClientLocation']['Subdivision'],
            'Metro': item['ClientLocation']['Metro'],
            'City': item['ClientLocation']['City'],
            'Latitude': item['ClientLocation']['Latitude'],
            'Longitude': item['ClientLocation']['Longitude'],
            'EventType': item['EventType'],
            'EventStatus': item['EventStatus']
        }
        if data["EventStatus"]=="RESOLVED":
            data["EndedAt"] = item['EndedAt'].strftime(time_format)
        result.append(data)
    while response.get('NextToken'):
        response = client.list_internet_events(
            NextToken=response['NextToken'],
            MaxResults=100,
        )
        for item in response['InternetEvents']:
            data = {
              'RefreshTime': refresh_time,
              'EventId': item['EventId'],
              'StartedAt': item['StartedAt'].strftime(time_format),
              'ASName': item['ClientLocation']['ASName'],
              'ASNumber': item['ClientLocation']['ASNumber'],
              'Country': item['ClientLocation']['Country'],
              'Subdivision': item['ClientLocation']['Subdivision'],
              'Metro': item['ClientLocation']['Metro'],
              'City': item['ClientLocation']['City'],
              'Latitude': item['ClientLocation']['Latitude'],
              'Longitude': item['ClientLocation']['Longitude'],
              'EventType': item['EventType'],
              'EventStatus': item['EventStatus']
            }
            if data["EventStatus"]=="RESOLVED":
                data["EndedAt"] = item['EndedAt'].strftime(time_format)
            result.append(data)
    upload_to_s3(os.getenv('BucketName'), f'events/{datetime.utcnow()}.json', result)

if __name__ == '__main__':
    lambda_handler({}, {})


