import sys
import time
import datetime
import boto3
import hashlib
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

args = getResolvedOptions(sys.argv,['year', 'month', 'cur-database', 'usage-account', 'region', 'work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
usage_account = args['usage_account'].strip()
region = args['region'].strip()
work_bucket = args['work_bucket'].strip()

cloudwatch = boto3.client("cloudwatch", region_name=region)
def load_rds_instance_metric(region, start_time, end_time, metric, stat='Average'):
    data = []
    paginator = cloudwatch.get_paginator('list_metrics')
    page_iterator = paginator.paginate(
        Namespace='AWS/RDS',
        MetricName=metric,
        Dimensions=[{'Name':'DBInstanceIdentifier'}]        
    )
    metrics = []
    for page in page_iterator:
        metrics += page["Metrics"]
    dbIds = list(set(map(lambda x: x["Dimensions"][0]["Value"], metrics)))
    batch = 10
    for x in range(0,len(dbIds), batch):
        metric_data_queries = list(map(lambda i: {
            'Id':f'i{hashlib.md5(i.encode("utf8")).hexdigest()}',
            'Label':i,
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/RDS',
                    'MetricName': metric,
                    'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': i}]
                },
                'Period': 3600,
                'Stat': stat 
            }
        }, dbIds[x:x+batch]))
        result = cloudwatch.get_metric_data(
            EndTime=end_time, 
            StartTime=start_time, 
            MaxDatapoints = 100800,
            MetricDataQueries=metric_data_queries
        )
        for value in result["MetricDataResults"]:
            for i,t in enumerate(value["Timestamps"]):
                timestr = t.strftime("%Y-%m-%dT%H:%M:%SZ")
                data.append({
                	"year": args["year"],
                	"month": f'{int(args["month"])}' ,
                	"region": region,
                	"usage_account": usage_account,
                    'dbId': value["Label"],
                    'usage_date': timestr,
                    metric: value["Values"][i]
                })
        return data

start = datetime.datetime(int(args["year"]),int(args["month"]),1,tzinfo=datetime.timezone.utc)
end = start + datetime.timedelta(days=31)
current_date = start
result = []    
while current_date <= end:
    next_date = current_date + datetime.timedelta(days=31)
    print(current_date, next_date)
    result += load_rds_instance_metric(region, current_date, next_date, 'ReadIOPS')
    result += load_rds_instance_metric(region, current_date, next_date, 'WriteIOPS')

    print(len(result))
    current_date = next_date
print(result[:3])

df_rdsmetrics = (spark.read.json(sc.parallelize(result))
    .withColumn("usage_date", to_timestamp("usage_date"))
    .groupBy(["year", "month", "usage_date", "region", "usage_account", "dbId"])
    .agg(sum("ReadIOPS"),sum("WriteIOPS"))
    .withColumn("io_cnt", (col("sum(ReadIOPS)")+col("sum(WriteIOPS)"))*3600)
)
(df_rdsmetrics.coalesce(1).write
    .mode("overwrite")
    .partitionBy(["usage_account","year","month","region"])
    .option("path", f"s3://{work_bucket}/data/rdsmetrics/res/")
    .saveAsTable(f"{cur_database}.enhanced_cur_rdsmetrics")
)

print(f"Job finished.")
job.commit()