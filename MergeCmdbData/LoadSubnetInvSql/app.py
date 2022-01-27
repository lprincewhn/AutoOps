import os
import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    cmdb_bucket = os.getenv("CMDB_DATA_BUCKET")
    athea_query_result_bucket = os.getenv("ATHENA_RESULT_BUCKET")
    athena_data_catalog = os.getenv("AthenaDataCatalog")
    startdate =  datetime.datetime.strptime(event["time"][:10], '%Y-%m-%d')
    subnet_inv_sql = os.getenv("SUBNET_INV_SQL")

    subnetQueryString = f"CREATE TABLE \"AwsDataCatalog\".\"default\".\"subnet_instances-{startdate:%Y-%m-%d}\" WITH (external_location = 's3://{cmdb_bucket}/subnet/region={event['region']}/day={startdate.day:02}/month={startdate.month:02}/year={startdate.year:02}/',format = 'ORC') AS " + subnet_inv_sql
    return {
        "athea_query_result_path": f's3://{athea_query_result_bucket}/',
        "subnetCreate": subnetQueryString,
        "subnetDrop": f"DROP TABLE `subnet_instances-{startdate:%Y-%m-%d}`"
    } 
