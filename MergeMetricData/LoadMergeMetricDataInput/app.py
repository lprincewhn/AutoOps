import os
import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    metrics_bucket = os.getenv("METRIC_DATA_BUCKET")
    athea_query_result_bucket = os.getenv("ATHENA_RESULT_BUCKET")
    athena_data_catalog = os.getenv("AthenaDataCatalog")
    startdate =  datetime.datetime.strptime(event["time"][:10], '%Y-%m-%d') - datetime.timedelta(2)
    enddate = datetime.datetime.strptime(event["time"][:10], '%Y-%m-%d') - datetime.timedelta(1)
    
    queryString = f"CREATE TABLE \"AwsDataCatalog\".\"default\".\"metric-{startdate:%Y-%m-%d}\" WITH (external_location = 's3://{metrics_bucket}/day={startdate.day:02}/month={startdate.month:02}/year={startdate.year:02}/region={event['region']}/',format = 'ORC') AS select namespace,metric_name,dimensions,period,timestamp,value,statistic from \"lambda:{athena_data_catalog}\".\"default\".metric_samples where (metric_name='CPUUtilization' AND namespace IN ('AWS/EC2', 'AWS/RDS', 'AWS/ElastiCache')) AND statistic IN ('Average') AND period = 300 AND timestamp BETWEEN To_unixtime(date '{startdate:%Y-%m-%d}' ) AND To_unixtime(date '{enddate:%Y-%m-%d}' )"
    return {
        "athea_query_result_path": f's3://{athea_query_result_bucket}/',
        "create": queryString,
        "drop": f"DROP TABLE `metric-{startdate:%Y-%m-%d}`"
    } 


