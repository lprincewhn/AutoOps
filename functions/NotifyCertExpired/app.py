import os
import json
import boto3
import traceback

def lambda_handler(event, context):

    print(f'Input: {json.dumps(event)}')
    client = boto3.client('acm')
    response = client.describe_certificate(
        CertificateArn=event.get('resourceId')
    )
    print(f'Response: {response}')
    in_use_by = response['Certificate']['InUseBy']
    event['message']=f'以下证书即将过期:\n\t证书ARN: {event.get("resourceId")}\n\t过期时间: {event.get("annotation")}\n\n关联资源:\n'
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
                event['message'] += f'\t{r}\t域名: {",".join(cnames)}\n'           
            else:
                event['message'] += f'\t{r}\n'
        except Exception as e:
            traceback.print_exc()
            event['message'] += f'\t{r}\n'
    client = boto3.client('sns')
    response = client.publish(
        TopicArn=os.getenv('SNS_TOPIC'),
        Subject='证书过期提醒',
        Message=event['message']
    )
    print(f'Response: {response}')
    return event 
