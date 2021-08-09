import os
import datetime
import logging


logging.basicConfig()
logger = logging.getLogger("ComplianceProcessor")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    distributionId = None
    eventName = event.get('detail').get('eventName')
    operation = None
    if eventName.startswith('Create'):
        operation = 'created'
        distributionId = event["detail"]["responseElements"]["distribution"]["id"]
        distributionArn = event["detail"]["responseElements"]["distribution"]["aRN"]
        aliases = event["detail"]["responseElements"]["distribution"]["distributionConfig"]["aliases"].get("items", [])
        aliases.sort()
    if eventName.startswith('Delete'):
        operation = 'deleted'
        distributionId = event["detail"]["requestParameters"]["id"]
        distributionArn = None
        aliases = []
    identityName = None
    userIdentity = event["detail"]["userIdentity"]
    if userIdentity['type'] == 'IAMUser':
        identityName = userIdentity["userName"]
    if userIdentity['type'] == 'IAMRole':
        identityName = userIdentity["sessionContext"]["sessionIssuer"]["userName"]
    return {
        'IdentityType': userIdentity['type'], 
        'IdentityName': identityName, 
        'DistributionArn': distributionArn, 
        'DistributionId': distributionId,
        'DomainName': '/'.join(aliases),
        'operation': operation
    }
