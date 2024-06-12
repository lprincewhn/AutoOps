import os
import json
import boto3
import traceback

def lambda_handler(event, context):
    print(f'Event In: {event}')
    message = '' 
    resources = event.get('resources')
    for certArn in resources:
        client = boto3.client('acm')
        response = client.describe_certificate(
            CertificateArn = certArn 
        )
        print(f'Response: {response}')
        in_use_by = response['Certificate']['InUseBy']
        message += f'证书ARN: {certArn} 将于{int(event.get("daysToExpiry"))}天后过期。\n关联资源:\n'
        client = boto3.client('cloudfront')
        for r in in_use_by:
            try:
                if 'cloudfront' in r:
                    id = r.split('/')[-1]
                    response = client.get_distribution_config(
                        Id=id
                    )
                    print(f'Response: {response}')
                    cnames =  response['DistributionConfig']['Aliases']['Items']  
                    message += f'\t{r}\t域名: {",".join(cnames)}\n'           
                else:
                    message += f'\t{r}\n'
            except Exception as e:
                traceback.print_exc()
                message += f'\t{r}\n'
        message += '\n'
    if message:
        event['message'] = message 
    print(f'Event Out: {event}')
    return event 
