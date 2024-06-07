import os
import json
import boto3
import logging
import datetime
import requests
from WXBizMsgCrypt3 import WXBizMsgCrypt
import xml.etree.ElementTree as ET

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
    
def send_msg(msg):
    # 入参msg有可能是字符串也有可能是对象，对象时需要将其转换成字符串发送
    secret = get_secret()
    req = requests.post("https://qyapi.weixin.qq.com/cgi-bin/gettoken", params=secret)
    logger.info(f'Token: {req.text}')
    result = json.loads(req.text)
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + result["access_token"] 
    logger.info(f'Url: {url}')
    body = {
        "touser" : "@all",
        "msgtype": "text",
        "agentid": secret["agentid"],
        "text":{
            "content": msg if type(msg)==str else json.dumps(msg, indent=2, ensure_ascii=False)
        },
        "safe":"0"
    }
    req = requests.post(url, json.dumps(body).encode('utf-8'))
    return json.loads(req.text)
    
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    secret = get_secret()
    crypto = WXBizMsgCrypt(secret.get("bottoken"), secret.get("botaeskey"), secret.get("corpid"))
    ret, xml_content = crypto.DecryptMsg(
      event.get("body"),
      event.get("queryStringParameters").get("msg_signature"), 
      event.get("queryStringParameters").get("timestamp"), 
      event.get("queryStringParameters").get("nonce")
    )
    root = ET.fromstring(xml_content.decode("utf-8"))
    request_data = {
        "SessionId": "current",
        "ToUserName": root.find("ToUserName").text,
        "FromUserName": root.find("FromUserName").text,
        "CreateTime": root.find("CreateTime").text,
        "MsgType": root.find("MsgType").text,
        "MsgId": root.find("MsgId").text,
        "AgentID": root.find("AgentID").text
    }
    if request_data["MsgType"] == "text":
        request_data["RequestContent"] = root.find("Content").text
    elif request_data["MsgType"] == "image":
        request_data["RequestContent"] = root.find("PicUrl").text
    elif request_data["MsgType"] == "voice":
        request_data["MediaId"] = root.find("MediaId").text
        request_data["Format"] = root.find("Format").text
    else:
        request_data["RequestContent"] = "1"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('wechat-bedrock')
    response = table.put_item(
      Item=request_data
    )
    logger.info(f"Inserted to DynamoDB: {request_data}")
    
    response = {
      "statusCode": 200,
      "headers": {
        "Content-Type": "application/xml"
      },
      "isBase64Encoded": False,
      "multiValueHeaders": { 
        "X-Custom-Header": ["My value", "My other value"],
      },
      "body": ""
    }
    return response

if __name__ == '__main__':
    lambda_handler({}, {})


