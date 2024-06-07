import requests
import json
import boto3
import logging
import os

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
    print(req.text)
    result = json.loads(req.text)
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + result["access_token"] 
    print(url)
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
    print(req.text)
    return json.loads(req.text)

def lambda_handler(event, context):
    print(f'Event In: {event}')
    message = event["Records"][0]["Sns"]["Message"]
    # EventBridge中的Input Transformer会将对象转成字符串进行传输，因此使用Input Transformer时message是字符串，不使用Input Transformer时message是对象，如果是字符串的话，尝试恢复成对象。
    try:
        message = json.loads(message)
    except:
        pass
    res = send_msg(message)
    print(f'Result: {res}')
