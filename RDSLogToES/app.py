import os
import re
import boto3
import json
import datetime
import requests
import base64
import logging

logging.basicConfig()
logger = logging.getLogger("RDSLogToES")
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

rds = boto3.client('rds')
firehose = boto3.client('firehose')

def deliverMysqlGeneralLogToES(dbid, filename):
    marker = '0'
    # Kinesis Firehose每次最多接受500条记录, 因此分批下载日志，每批500行，当返回行数>=500时，继续下载，小于500时表示下载完毕。
    cnt_response = 500
    while cnt_response>=500: 
        file_resp = rds.download_db_log_file_portion(
            DBInstanceIdentifier=dbid,
            LogFileName=filename,
            Marker=marker,
            NumberOfLines=500
        )
        logs = file_resp['LogFileData'].split('\n')
        records = []
        for i in logs:
            logger.debug(f"Item: {i}")
            # 数据行以年份开头，因此第一个字符必须为数字
            if re.match(r'^[0-9]', i):
                ary = i.split()
                record = {}
                record['timestamp'] = datetime.datetime.strptime(ary[0][:23], '%Y-%m-%dT%H:%M:%S.%f').timestamp()*1000
                record['database_id'] = dbid
                record['id'] = ary[1]
                record['command'] = ary[2]
                if len(ary) >= 4:
                    record['argument'] = ' '.join(ary[3:])
                data = base64.b64encode(json.dumps(record).encode('utf-8'))
                records.append({'Data': data})
            else:
                logger.info(i)
        # 发送到Kinesis Firehose
        if records:
            response = firehose.put_record_batch(
                DeliveryStreamName='rds-general-log',
                Records=records
            )
            logger.info(f'Response: {json.dumps(response)[:100]}...')
        marker = file_resp['Marker']
        cnt_response = len(logs)
        logger.info(f'{len(records)} of {len(logs)} lines delivered.')


def deliverMysqlAuditLogToES(dbid, filename):
    marker = '0'
    # Kinesis Firehose每次最多接受500条记录, 因此分批下载日志，每批500行，当返回行数>=500时，继续下载，小于500时表示下载完毕。
    cnt_response = 500
    while cnt_response>=500: 
        file_resp = rds.download_db_log_file_portion(
            DBInstanceIdentifier=dbid,
            LogFileName=filename,
            Marker=marker,
            NumberOfLines=500
        )
        logs = file_resp['LogFileData'].split('\n')
        records = []
        for i in logs:
            logger.info(f"Item: {i}")
            # 数据行以年份开头，因此第一个字符必须为数字
            # if re.match(r'^[0-9]', i):
            #     ary = i.split()
            #     record = {}
            #     record['timestamp'] = datetime.datetime.strptime(ary[0][:23], '%Y-%m-%dT%H:%M:%S.%f').timestamp()*1000
            #     record['database_id'] = dbid
            #     record['id'] = ary[1]
            #     record['command'] = ary[2]
            #     if len(ary) >= 4:
            #         record['argument'] = ' '.join(ary[3:])
            #     data = base64.b64encode(json.dumps(record).encode('utf-8'))
            #     records.append({'Data': data})
            # else:
            #     logger.info(f'Skip item: {i}')
        # 发送到Kinesis Firehose
        if records:
            response = firehose.put_record_batch(
                DeliveryStreamName='rds-general-log',
                Records=records
            )
            logger.info(f'Response: {json.dumps(response)[:100]}...')
        marker = file_resp['Marker']
        cnt_response = len(logs)
        logger.info(f'{len(records)} of {len(logs)} lines delivered.')

def lambda_handler(event, context):
    logger.info(f'Event In: {json.dumps(event)}...')
    dbid = os.getenv('DBID')
    response = rds.describe_db_log_files(
        DBInstanceIdentifier=dbid,
        FileLastWritten=int((datetime.datetime.now() - datetime.timedelta(hours=1)).timestamp()*1000)
    )
    filenames = event.get('filenames', list(map(lambda x: x.get('LogFileName'), response['DescribeDBLogFiles']))) 
    for filename in filenames:
        if not re.match(r'.+[0-9]$', filename):
            continue
        logger.info(f'Processing {filename}...')
        if filename.startswith('general'):
            deliverMysqlGeneralLogToES(dbid, filename)
        if filename.startswith('audit'):
            deliverMysqlAuditLogToES(dbid, filename)

if __name__ == '__main__':
    lambda_handler({}, None)
