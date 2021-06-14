import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Event In: {event}')
    print(f'Environment TAGS_TO_CHECK: {os.getenv("TAGS_TO_CHECK")}')
    client = boto3.client('ec2')
    nextToken = ''
    message = ''
    while nextToken != None:
        response = client.describe_instances(NextToken=nextToken)
        print(f'Response: {response}')
        for r in response['Reservations']:
            for i in r['Instances']:
                instanceId = i['InstanceId']
                print(instanceId)
                # EC2实例上包含的TAG，包含Key和Value
                tags_on_ec2 = i.get('Tags', [])
                print(f'EC2 tags: {tags_on_ec2}')
                # 需要检查的TAG列表
                tags_to_check = list(filter(lambda m:m, map(lambda x:x.strip(), os.getenv('TAGS_TO_CHECK', '').split(','))))
                print(f'Tags to check: {tags_to_check}')
                tags_not_comliance = tags_to_check.copy()
                for t in tags_to_check:
                    for t1 in tags_on_ec2:
                        if t1.get('Key') == t and t1.get('Value'):
                            tags_not_comliance.remove(t)
                            break
                if tags_not_comliance:
                    message += f'区域 {os.getenv("AWS_REGION")}, 实例 {instanceId} 的 {",".join(tags_not_comliance)} 标签不合规\n' 
        nextToken = response.get('NextToken')
        print(f'nextToken: {nextToken}')
    print(message)
    if message:
        event['message'] = message
        event['subject'] = '【AWS通知】标签不合规'
    return event

if __name__ == '__main__':
    lambda_handler({}, None)
