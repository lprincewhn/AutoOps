import os
import json
import time
import boto3
import base64
import logging
import datetime
import requests
import traceback
from WXBizMsgCrypt3 import WXBizMsgCrypt
from boto3.dynamodb.conditions import Key,Attr
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'))
logger.addHandler(ch)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('wechat-bedrock')

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(
        SecretId="wechat_secret"
    )
    if 'SecretString' in response:
        secret = json.loads(response['SecretString'])
        return secret
    return None
    
def send_msg(touser, msg):
    # 入参msg有可能是字符串也有可能是对象，对象时需要将其转换成字符串发送
    secret = get_secret()
    req = requests.post("https://qyapi.weixin.qq.com/cgi-bin/gettoken", params=secret)
    logger.info(f'Token: {req.text}')
    result = json.loads(req.text)
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + result["access_token"] 
    logger.info(f'Url: {url}')
    body = {
        "touser" : touser,
        "msgtype": "text",
        "agentid": secret["agentid"],
        "text":{
            "content": msg if type(msg)==str else json.dumps(msg, indent=2, ensure_ascii=False)
        },
        "safe":"0"
    }
    req = requests.post(url, json.dumps(body).encode('utf-8'))
    logger.info(f'SendMessage Response: {req.text}')
    return json.loads(req.text)

def get_media(mediaid):
    secret = get_secret()
    req = requests.post("https://qyapi.weixin.qq.com/cgi-bin/gettoken", params=secret)
    logger.info(f'Token: {req.text}')
    result = json.loads(req.text)
    url = "https://qyapi.weixin.qq.com/cgi-bin/media/get?access_token=" + result["access_token"] + "&media_id=" + mediaid
    logger.info(f'Url: {url}')
    req = requests.get(url)
    return req.content
    
def voice2text(job_name, media_id, media_format):
    media_content = get_media(media_id)
    s3_bucket_name = os.getenv('MEDIA_BUCKET')
    s3 = boto3.client('s3')
    s3.put_object(Body=media_content, Bucket=s3_bucket_name, Key=f'voice-{job_name}')
    transcribe = boto3.client('transcribe')
    language_code = 'zh-CN'
    logger.info(f"Starting transcription job {job_name}")
    response = transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        LanguageCode=language_code,
        MediaFormat=media_format,
        Media={
            'MediaFileUri': f's3://{s3_bucket_name}/voice-{job_name}'
        },
        OutputBucketName=s3_bucket_name
    )
    logger.info(f"Transcription job {job_name} started: {response['TranscriptionJob']['TranscriptionJobStatus']}")
    while True:
        time.sleep(1)
        job_status = transcribe.get_transcription_job(TranscriptionJobName=job_name)['TranscriptionJob']['TranscriptionJobStatus']
        logger.info(f"Transcription job {job_name} status: {job_status}")
        if job_status in ['COMPLETED', 'FAILED']:
            break
        continue
    if job_status == 'COMPLETED':
        transcription_result_url = transcribe.get_transcription_job(TranscriptionJobName=job_name)['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcription_result_obj = s3.get_object(Bucket=s3_bucket_name, Key=os.path.basename(transcription_result_url))
        transcription_result = json.loads(transcription_result_obj['Body'].read().decode('utf-8'))
        logger.info(f"Transcription job  {job_name} result: {transcription_result}")
        return transcription_result["results"]["transcripts"][0]["transcript"]
    else:
        logger.error(f"Transcription job {job_name} failed.")
            
def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}')
    secret = get_secret()
    for record in event.get("Records"):
      try:
        if record.get("eventName")=='INSERT':
          item = {k: v.get("S") for k, v in record.get("dynamodb").get("NewImage").items()}
          if item["MsgType"] == 'voice' and not item.get("RequestContent"):
            job_name = item["MsgId"]
            media_id = item["MediaId"]
            media_format = item["Format"]
            item["RequestContent"] = voice2text(job_name, media_id, media_format)
            response = table.put_item(
              Item=item
            )
            logger.info("Updated DynamoDB with RequestContent.")
          response = table.query(
            IndexName='FromUserName-SessionId',
            KeyConditionExpression=Key('FromUserName').eq(item["FromUserName"]) & Key('SessionId').eq("current")
          )
          logger.info(f'Dynamodb query response: {response}')
          if item["RequestContent"].strip() == '1':
            new_session_id = str(datetime.datetime.now().timestamp())
            for item in response['Items']:
              item['SessionId'] = new_session_id
              response = table.put_item(
                Item=item
              )
              logger.info("Updated DynamoDB with new SessionId.")
            send_msg(item["FromUserName"], '已清除会话')
          else:
            bedrock_request = {
              "anthropic_version": "bedrock-2023-05-31",
              "max_tokens": 1024,
              "messages": []
            }
            sorted_content = sorted(response['Items'], key=lambda x: x["CreateTime"])
            for item in list(sorted_content):
              if item["RequestContent"].strip() == '1':
                continue
              elif item["MsgType"] == 'text' or item["MsgType"] == 'voice':
                bedrock_request['messages'].append(
                  {
                    "role": "user",
                    "content": [{"type": "text", "text": item.get("RequestContent")}]
                  }
                )
              elif item["MsgType"] == 'image':
                response = requests.get(item.get("RequestContent"))
                encoded_image = base64.b64encode(response.content).decode('utf-8')
                bedrock_request['messages'].append(
                  {
                    "role": "user",
                    "content": [
                      {"type": "text", "text": '请描述图片'},
                      {"type": "image", "source": { "type": "base64", "media_type": "image/jpeg", "data": encoded_image }}
                    ]
                  }
                )
              if  item.get("ResponseContent"):
                bedrock_request['messages'].append(
                  {
                    "role": "assistant",
                    "content": [{"type": "text", "text": item.get("ResponseContent")}]
                  }
                )
            logger.info(f'User: {json.dumps(bedrock_request)}')
            client = boto3.client('bedrock-runtime', region_name='us-east-1')
            response = client.invoke_model(
              body=json.dumps(bedrock_request).encode('utf-8'),
              modelId='anthropic.claude-3-haiku-20240307-v1:0'
            )
            logger.info(f"Got Bedrock response: {response}")
            
            bedrock_result = json.loads(response.get("body").read().decode('utf-8'))
            logger.info(f'Assistant: {json.dumps(bedrock_result)}')
            
            item["ResponseContent"] = bedrock_result["content"][-1]["text"]
            item["InputToken"] = bedrock_result["usage"]["input_tokens"]
            item["OutputToken"] = bedrock_result["usage"]["output_tokens"]
            send_msg(item["FromUserName"], item["ResponseContent"])
            
            response = table.put_item(
              Item=item
            )
            logger.info("Updated DynamoDB with ResponseContent.")
      except:
        logger.error(f'Fail to process {record}')
        traceback.print_exc()
        continue
    
if __name__ == '__main__':
    lambda_handler({}, {})


