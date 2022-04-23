import os
import datetime
import logging


logging.basicConfig()
logger = logging.getLogger("CloudFrontProvision")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

def lambda_handler(event, context):
    logger.info(f'Event In: {event}')
    distributionId = None
    eventName = event.get('detail').get('eventName')
    aliases = [] 
    if eventName.startswith('Create'):
        event['DistributionId'] = event["detail"]["responseElements"]["distribution"]["id"]
        event['DistributionArn'] = event["detail"]["responseElements"]["distribution"]["aRN"]
        aliases = event["detail"]["responseElements"]["distribution"]["distributionConfig"]["aliases"].get("items", [])
        aliases.sort()
    if eventName.startswith('Update'):
        event['DistributionId'] = event["detail"]["responseElements"]["distribution"]["id"]
        event['DistributionArn'] = event["detail"]["responseElements"]["distribution"]["aRN"]
        aliases = event["detail"]["responseElements"]["distribution"]["distributionConfig"]["aliases"].get("items", [])
        aliases.sort()
    if eventName.startswith('Delete'):
        event['DistributionId'] = event["detail"]["requestParameters"]["id"]
        event['DistributionArn'] = None
    event['DomainName'] = '/'.join(aliases)
    identityName = None
    userIdentity = event["detail"]["userIdentity"]
    event['IdentityType'] = userIdentity['type'] 
    if userIdentity['type'] == 'IAMUser':
        event['IdentityName'] = userIdentity["userName"]
    if userIdentity['type'] == 'IAMRole':
        evnet['IdentityName'] = userIdentity["sessionContext"]["sessionIssuer"]["userName"]
    
    return event 
