import os
import time
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('ssm')
    response = client.send_command(
        InstanceIds=[
            event.get('InstanceId'),
        ],
        DocumentName=os.getenv('SSM_DOCNAME'),
        DocumentVersion='$DEFAULT',
        TimeoutSeconds=30,
        Comment=event.get('Comment', ''),
        Parameters={}
    )
    print(f'Response: {response}')
    commandId = response.get('Command').get('CommandId')
    time.sleep(10)
    invokation_status = 'InProgress'
    response = None
    while invokation_status == 'InProgress':
        response = client.get_command_invocation(
            CommandId=commandId,
            InstanceId=event.get('InstanceId')
        )
        print(f'Response: {response}')
        invokation_status = response.get('Status')
        time.sleep(10)
    if invokation_status == 'Success':
        output = response.get('StandardOutputContent')
        if len(output) == 24000:
            raise Exception('Too long output')
        event['Volumes'] = []
        for line in output.split('\n'):
            if line.startswith('/dev/'):
                event['Volumes'].append({
                    'device': line.split()[0].lstrip('/dev/'), 
                    'path': line.split()[6],
                    'fstype': line.split()[1]
                })
        return event
    raise Exception('SSM Command failed') 
