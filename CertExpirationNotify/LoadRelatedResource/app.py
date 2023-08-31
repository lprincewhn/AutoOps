import os
import json
import boto3
import logging
import traceback

logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.INFO, force=True)
if os.getenv("DEBUG", None):
    logging.info("Set logging level to DEBUG")
    logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', level=logging.DEBUG, force=True)

def lambda_handler(event, context):
    logging.info(f'Event In: {json.dumps(event)}')
    resources = event.get('resources')
    daysToExpiry = event.get('detail').get('DaysToExpiry')
    client = boto3.client('acm')
    event['linked_resources'] = {}
    for certArn in resources:
        response = client.describe_certificate(
            CertificateArn = certArn
        )
        in_use_by = response['Certificate']['InUseBy']
        cloudfront = boto3.client('cloudfront')
        linked_resources = []
        for r in in_use_by:
            try:
                if 'cloudfront' in r:
                    id = r.split('/')[-1]
                    response = cloudfront.get_distribution_config(
                        Id=id
                    )
                    cnames =  response['DistributionConfig']['Aliases']['Items']
                    linked_resources.append({'resourceArn': r, 'CNames': cnames})    
                else:
                    linked_resources.append({'resourceArn': r})
            except Exception as e:
                traceback.print_exc()
        event['linked_resources'][certArn] = linked_resources
    event['daysToExpiry'] = daysToExpiry
    logging.info(f'Event Out: {json.dumps(event)}')
    return event 
