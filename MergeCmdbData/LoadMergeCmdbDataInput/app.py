import os
import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    cmdb_bucket = os.getenv("CMDB_DATA_BUCKET")
    athea_query_result_bucket = os.getenv("ATHENA_RESULT_BUCKET")
    athena_data_catalog = os.getenv("AthenaDataCatalog")
    startdate =  datetime.datetime.strptime(event["time"][:10], '%Y-%m-%d')

    
    ec2QueryString = f"CREATE TABLE \"AwsDataCatalog\".\"default\".\"ec2_instances-{startdate:%Y-%m-%d}\" WITH (external_location = 's3://{cmdb_bucket}/ec2/region={event['region']}/day={startdate.day:02}/month={startdate.month:02}/year={startdate.year:02}/',format = 'ORC') AS select i.instance_id, n.project, image_id, instance_type, platform, vpc_id, subnet_id, private_ip_address, public_ip_address, security_groups, security_group_names, key_name,cardinality(network_interfaces) as eni_count from \"lambda:{athena_data_catalog}\".\"ec2\".ec2_instances i left join (select instance_id,t.tag.value as project from \"lambda:{athena_data_catalog}\".\"ec2\".ec2_instances i CROSS JOIN UNNEST(i.tags) as t(tag) where t.tag.key='Project') n on i.instance_id=n.instance_id"
    rdsQueryString = f"CREATE TABLE \"AwsDataCatalog\".\"default\".\"rds_instances-{startdate:%Y-%m-%d}\" WITH (external_location = 's3://{cmdb_bucket}/rds/region={event['region']}/day={startdate.day:02}/month={startdate.month:02}/year={startdate.year:02}/',format = 'ORC') AS select i.instance_id, n.project, instance_class, engine, engine_version, primary_az, secondary_az, read_replica_source_id, endpoint from \"lambda:{athena_data_catalog}\".\"rds\".rds_instances i left join (select instance_id,t.tag.value as project from \"lambda:{athena_data_catalog}\".\"rds\".rds_instances i CROSS JOIN UNNEST(i.tags) as t(tag) where t.tag.key='Project') n on i.instance_id=n.instance_id"
    return {
        "athea_query_result_path": f's3://{athea_query_result_bucket}/',
        "ec2Create": ec2QueryString,
        "ec2Drop": f"DROP TABLE `ec2_instances-{startdate:%Y-%m-%d}`",
        "rdsCreate": rdsQueryString,
        "rdsDeop": f"DROP TABLE `rds_instances-{startdate:%Y-%m-%d}`"
    } 
