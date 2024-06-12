import os
import json
import boto3
import datetime
import logging


logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    invokingEvent = json.loads(event['invokingEvent'])
    logger.info(f'invokingEvent: {invokingEvent}')
    if invokingEvent['messageType'] == 'ConfigurationItemChangeNotification' and invokingEvent['configurationItem']['configuration']:
        ruleParameters = json.loads(event.get('ruleParameters','{}'))
        logger.info(f'ruleParameters: {ruleParameters}')
        configRuleArn = event['configRuleArn']
        configRuleName = event['configRuleName']
        userName = invokingEvent['configurationItem']['configuration']['userName']
        logger.info(f'userName: {userName}')
        groupList = invokingEvent['configurationItem']['configuration']['groupList']
        logger.info(f'groupList: {groupList}')
        requiredGroupList = ruleParameters.get('requiredGroupList', '').split(',')
        logger.info(f'requiredGroupList: {requiredGroupList}')
        exemptedUserList = ruleParameters.get('exemptedUserList', '').split(',')
        logger.info(f'exemptedUserList: {exemptedUserList}')
        notCompliantGroups = set(requiredGroupList) - set(groupList)
        logger.info(f'notCompliantGroups: {notCompliantGroups}')
        client = boto3.client('config')
        if notCompliantGroups and (not userName in exemptedUserList):
            annotation = f'{userName}不在{",".join(notCompliantGroups)}组。'
            response = client.put_evaluations(
                Evaluations=[
                    {
                        'ComplianceResourceType': invokingEvent['configurationItem']['resourceType'],
                        'ComplianceResourceId': invokingEvent['configurationItem']['resourceId'],
                        'ComplianceType': 'NON_COMPLIANT',
                        'Annotation': annotation,
                        'OrderingTimestamp': datetime.datetime.now()
                    },
                ],
                ResultToken=event['resultToken']
            )
            logger.info(response)
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
            logger.info(response)
    return {
        'statusCode': 200,
    }


