import requests
import json
import boto3

tokenUrl = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"

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
    secret = get_secret() 
    req = requests.post(tokenUrl, params=secret)
    token = json.loads(req.text)
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + token["access_token"] 
    print(url)
    body = """{"touser" : "@all" ,
      "msgtype":"text",
      "agentid":"%s",
      "text":{
        "content": "%s"
      },
      "safe":"0"
      }""" % (secret["agentid"], msg)
    return requests.post(url, body.encode('utf-8'))

def lambda_handler(event, context):
    print(f'Event In: {event}')
    message = event["Records"][0]["Sns"]["Message"]
    res = send_msg(message)
    print(f'Response: {res}')
    return json.loads(res.text)
