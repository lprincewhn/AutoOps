import os
import json
import boto3
import logging
from WXBizMsgCrypt3 import WXBizMsgCrypt

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(
        SecretId="wechat_secret"
    )
    if 'SecretString' in response:
        secret = json.loads(response['SecretString'])
        return secret
    return None
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    secret = get_secret()
    verify = WXBizMsgCrypt(secret.get("bottoken"), secret.get("botaeskey"), secret.get("corpid"))
    ret, echostr = verify.VerifyURL(
      event.get("queryStringParameters").get("msg_signature"), 
      event.get("queryStringParameters").get("timestamp"), 
      event.get("queryStringParameters").get("nonce"), 
      event.get("queryStringParameters").get("echostr")
    )
    print(ret, echostr)
    response = {
      "statusCode": 200,
      "headers": {
        "Content-Type": "application/text"
      },
      "isBase64Encoded": False,
      "multiValueHeaders": { 
        "X-Custom-Header": ["My value", "My other value"],
      },
      "body": echostr
    }
    return response

if __name__ == '__main__':
    lambda_handler({}, {})


