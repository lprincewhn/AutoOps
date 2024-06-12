import os
import boto3
import zlib 
import json
import base64
import requests
import datetime
import logging
import aws_encryption_sdk
from aws_encryption_sdk import CommitmentPolicy
from aws_encryption_sdk.internal.crypto import WrappingKey
from aws_encryption_sdk.key_providers.raw import RawMasterKeyProvider
from aws_encryption_sdk.identifiers import WrappingAlgorithm, EncryptionKeyType
from requests_aws4auth import AWS4Auth

logging.basicConfig()
logger = logging.getLogger("AuroraDASTransform")
print(os.getenv("DEBUG", None))
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

class AuroraDasMasterKeyProvider(RawMasterKeyProvider):
    provider_id = "BC"

    def __new__(cls, *args, **kwargs):
        obj = super(RawMasterKeyProvider, cls).__new__(cls)
        return obj

    def __init__(self, plain_key):
        RawMasterKeyProvider.__init__(self)
        self.wrapping_key = WrappingKey(wrapping_algorithm=WrappingAlgorithm.AES_256_GCM_IV12_TAG16_NO_PADDING,
                                        wrapping_key=plain_key, wrapping_key_type=EncryptionKeyType.SYMMETRIC)

    def _get_raw_key(self, key_id):
        return self.wrapping_key

def decrypt_payload(payload, data_key):
    key_provider = AuroraDasMasterKeyProvider(data_key)
    key_provider.add_master_key("DataKey")
    enc_client = aws_encryption_sdk.EncryptionSDKClient(commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_ALLOW_DECRYPT)
    decrypted_plaintext, header = enc_client.decrypt(
        source=payload,
        materials_manager=aws_encryption_sdk.materials_managers.default.DefaultCryptoMaterialsManager(master_key_provider=key_provider))
    return zlib.decompress(decrypted_plaintext, zlib.MAX_WBITS + 16)    

def deliverToES(data):
    es_region = os.getenv("ESRegion")
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, es_region, 'es', session_token=credentials.token)
    host = os.getenv("ESEndpoint")
    headers = { "Content-Type": "application/json" }
    url = host + '/_bulk'
    logger.info(f'URL: {url}')
    logger.debug(f'DATA: {data}')
    r = requests.post(url, auth=awsauth, data=data, headers=headers)
    logger.info(f'{r.text[:100]}...')

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)[:100]}...')
    logger.debug(f'Details: {json.dumps(event)}')
    kms = boto3.client('kms')
    request_data = ""
    for r in event['Records']:
        eventSourceARN = r['eventSourceARN']
        streamName = eventSourceARN.split('/')[1]
        clusterId = streamName.split('-')[4]
        aurora_resource_id = f'cluster-{clusterId}'
        region = r['awsRegion']
        record_data=json.loads(base64.b64decode(r['kinesis']['data']).decode())
        payload_decoded = base64.b64decode(record_data['databaseActivityEvents'])
        data_key_decoded = base64.b64decode(record_data['key'])
        data_key_decrypt_result = kms.decrypt(CiphertextBlob=data_key_decoded, EncryptionContext={'aws:rds:dbc-id': aurora_resource_id})
        items = decrypt_payload(payload_decoded, data_key_decrypt_result['Plaintext'])
        logger.debug(f'Decoded Item: {json.loads(items)}')
        for i in json.loads(items)["databaseActivityEventList"]:
            # 此处可加入数据过滤逻辑
            index = None
            i["region"] = region
            i["clusterId"] = clusterId
            if i.get("startTime"):
                i["timestamp"] = datetime.datetime.strptime(f'{i["startTime"][:23]}', '%Y-%m-%d %H:%M:%S.%f').timestamp()*1000
                index = f'aurora-das-{i["startTime"][:10]}'
            else:
                i["timestamp"] = datetime.datetime.strptime(f'{i["logTime"][:23]}', '%Y-%m-%d %H:%M:%S.%f').timestamp()*1000
                index = f'aurora-das-{i["logTime"][:10]}'
            request_data += json.dumps({"index":{"_index" :index}}) + "\n"
            request_data += json.dumps(i) + "\n"
    deliverToES(request_data)



