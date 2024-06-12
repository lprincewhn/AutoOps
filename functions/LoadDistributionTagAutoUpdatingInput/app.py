import string
import datetime

def lambda_handler(event, context):
    print(f'Input: {event}')
    distribution_arn = event["detail"]["responseElements"]["distribution"]["aRN"]
    identityName = None
    userIdentity = event["detail"]["userIdentity"]
    if userIdentity['type'] == 'IAMUser':
        identityName = userIdentity["userName"]
    if userIdentity['type'] == 'IAMRole':
        identityName = userIdentity["sessionContext"]["sessionIssuer"]["userName"]
    return {'IdentityType': userIdentity['type'], 'IdentityName': identityName, 'DistributionArn': distribution_arn}
