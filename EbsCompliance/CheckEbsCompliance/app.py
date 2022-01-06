import os
import json
import boto3
import datetime
import logging


logging.basicConfig()
logger = logging.getLogger("EbsCompliance")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    invokingEvent = json.loads(event['invokingEvent'])
    logger.info(f'invokingEvent: {json.dumps(invokingEvent)}')
    if invokingEvent['configurationItem']['configuration']:
        configRuleArn = event['configRuleArn']
        configRuleName = event['configRuleName']
        volumeId = invokingEvent['configurationItem']['configuration']['volumeId']
        logger.info(f'volumeId: {volumeId}')
        tags = invokingEvent['configurationItem']['configuration']['tags']
        logger.info(f'tags: {tags}')
        tagkeys = list(map(lambda x:x['key'], filter(lambda x:x['value'], tags)))
        logger.info(f'tagkeys: {set(tagkeys)}')
        # Parameters
        ruleParameters = json.loads(event.get('ruleParameters','{}'))
        logger.info(f'ruleParameters: {ruleParameters}')
        requiredTagList = ruleParameters.get('requiredTagList', '').split(',')
        logger.info(f'requiredTagList: {requiredTagList}')
        exemptedVolumeList = ruleParameters.get('exemptedVolumeList', '').split(',')
        logger.info(f'exemptedVolume: {exemptedVolumeList}')
        notCompliantTags = set(requiredTagList) - set(tagkeys)
        logger.info(f'notCompliantTags: {notCompliantTags}')
        # Do evaluation
        annotation = None 
        if notCompliantTags and (not volumeId in exemptedVolumeList):
            annotation = f'{volumeId}的以下标签不合规: {",".join(notCompliantTags)}。'

        client = boto3.client('config')
        if annotation:
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


