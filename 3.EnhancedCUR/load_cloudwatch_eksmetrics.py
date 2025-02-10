import sys
import time
import datetime
import boto3
import requests
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import *
from awsglue.context import GlueContext
from awsglue.job import Job
  
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")  

args = getResolvedOptions(sys.argv,['year', 'month', 'cur-database', 'usage-account', 'region', 'container-insights-loggroup', 'work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
usage_account = args['usage_account'].strip()
region = args['region'].strip()
work_bucket = args['work_bucket'].strip()
container_insights_loggroup = args['container_insights_loggroup'].strip()

cloudwatch = boto3.client("logs", region_name=region)
start = datetime.datetime(int(args["year"]),int(args["month"]),1,tzinfo=datetime.timezone.utc)
end = start + datetime.timedelta(days=31)
current_date = start
result = []
queryString = f'''
filter !isempty(kubernetes.pod_name) 
| fields datefloor(Timestamp, 1h) as date, 
    concat(InstanceId,":pod/",ClusterName,"/",kubernetes.namespace_name,"/",kubernetes.pod_name) as resource_id, 
    ClusterName as eks_cluster_name,
    kubernetes.namespace_name as eks_namespace,
    kubernetes.labels.app as eks_app, 
    kubernetes.labels.project as project, 
    InstanceId as instance 
| stats min(Timestamp) as start_time, 
    max(Timestamp) as end_time, 
    count(pod_cpu_usage_total) as actual_cpu_cnt, 
    sum(pod_cpu_usage_total) as actual_cpu, 
    count(pod_cpu_request) as reserved_cpu_cnt, 
    sum(pod_cpu_request) as reserved_cpu, 
    count(pod_memory_working_set) as actual_mem_cnt, 
    sum(pod_memory_working_set) as actual_mem,
    count(pod_memory_request) as reserved_mem_cnt, 
    sum(pod_memory_request) as reserved_mem 
by date,resource_id,project,eks_cluster_name,eks_namespace,eks_app,instance
'''
print(f"Cloudwatch Log Insights Query: {queryString}.\n")
while current_date <= end:
    next_date = current_date + datetime.timedelta(days=10)
    print(f"Get metrics from {current_date} to {next_date}.\n")
    res = cloudwatch.start_query(
        logGroupName=container_insights_loggroup,
        startTime=int(current_date.timestamp()),
        endTime=int(next_date.timestamp()),
        queryString=queryString,
        limit=10000
    )
    queryId = res['queryId']
    status = 'Running'
    while status == 'Running':
        time.sleep(1)
        res = cloudwatch.get_query_results(
            queryId=queryId
        )
        status = res['status']
        print(status)
    for r in res['results']:
        item = {
        	"year": args["year"],
        	"month": f'{int(args["month"])}' ,
        # 	"charge_type": "ContainerUsage",
        	"region": region,
        	"usage_account": usage_account,
        }
        for f in r:
            if "cpu" in f.get("field") or "mem" in f.get("field"):
                item[f.get("field")] = float(f.get("value"))
            else:
                item[f.get("field")] = f.get("value")
        if item["date"][:7]==f'{args["year"]}-{args["month"]}':
            result.append(item)

    print(f"Got {len(result)} items. Statistics: {res['statistics']}, Status: {res['status']}.\n")
    current_date = next_date

if result:
    df_eksmetrics = spark.read.json(sc.parallelize(result)).withColumn("date", to_timestamp("date"))
    (df_eksmetrics.coalesce(1).write
        .mode("overwrite")
        .partitionBy(["usage_account","year","month","region"])
        .option("path", f"s3://{work_bucket}/data/eksmetrics_cloudwatch/res/")
        .saveAsTable(f"{cur_database}.enhanced_cur_eksmetrics_cloudwatch")
    )
    print(f"Job finished. {len(result)} rows was written into table {cur_database}.enhanced_cur_eksmetrics_cloudwatch.\n")
else:
    print(f"Result is empty.")
job.commit()