import json
import boto3
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    invokingEvent = json.loads(event['invokingEvent'])
    print(f'invokingEvent: {invokingEvent}')
    if invokingEvent['messageType'] == 'ConfigurationItemChangeNotification' and invokingEvent['configurationItem']['configuration']:
        ruleParameters = json.loads(event.get('ruleParameters','{}'))
        print(f'ruleParameters: {ruleParameters}')
        configRuleArn = event['configRuleArn']
        configRuleName = event['configRuleName']
        userName = invokingEvent['configurationItem']['configuration']['userName']
        print(f'userName: {userName}')
        groupList = invokingEvent['configurationItem']['configuration']['groupList']
        print(f'groupList: {groupList}')
        requiredGroupList = ruleParameters.get('requiredGroupList', '').split(',')
        print(f'requiredGroupList: {requiredGroupList}')
        exludedUserList = ruleParameters.get('exludedUserList', '').split(',')
        print(f'exludedUserList: {exludedUserList}')
        notCompliantGroups = set(requiredGroupList) - set(groupList)
        print(f'notCompliantGroups: {notCompliantGroups}')
        client = boto3.client('config')
        if notCompliantGroups and (not userName in exludedUserList):
            message = f'{userName}不在{",".join(notCompliantGroups)}组。'
            response = client.put_evaluations(
                Evaluations=[
                    {
                        'ComplianceResourceType': invokingEvent['configurationItem']['resourceType'],
                        'ComplianceResourceId': invokingEvent['configurationItem']['resourceId'],
                        'ComplianceType': 'NON_COMPLIANT',
                        'Annotation': message,
                        'OrderingTimestamp': datetime.datetime.now()
                    },
                ],
                ResultToken=event['resultToken']
            )
            print(response)
        else:
            response = client.put_evaluations(
                Evaluations=[
                    {
                        'ComplianceResourceType': invokingEvent['configurationItem']['resourceType'],
                        'ComplianceResourceId': invokingEvent['configurationItem']['resourceId'],
                        'ComplianceType': 'COMPLIANT',
                        'OrderingTimestamp': datetime.datetime.now()
                    },
                ],
                ResultToken=event['resultToken']   
            )
            print(response)
    return {
        'statusCode': 200,
    }


