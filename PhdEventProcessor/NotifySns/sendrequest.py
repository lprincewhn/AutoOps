import boto3
import gzip
import json
import datetime
import requests
from requests_aws4auth import AWS4Auth
import logging
try:
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection
HTTPConnection.debuglevel = 1

logging.basicConfig() # 初始化 logging，否则不会看到任何 requests 的输出。
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

region = 'us-east-1' 
service = 'states'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host = 'https://states.us-east-1.amazonaws.com' 

headers = { "Content-Type": "application/json" }

def lambda_handler(event, context):
    querystring = 'Action=SendTaskSuccess'
    querystring += '&Version=2010-05-08'
    querystring += '&X-Amz-Algorithm=AWS4-HMAC-SHA256'
    querystring += '&X-Amz-Credential= urlencode(credentials.access_key + '/' + credential_scope)
    querystring += &X-Amz-Date=date
    querystring += &X-Amz-Expires=timeout interval
    querystring += &X-Amz-SignedHeaders=signed_headers
    url = host + '/?Action=SendTaskSuccess&TaskToken=xxx&Output={}'
    print(f'URL: {url}')
    #r = requests.post(url, auth=awsauth, json=item, headers=headers)
    r = requests.get(url, auth=awsauth)
    print(r)
    print(r.text)

if __name__ == '__main__':
   lambda_handler(None, None)
