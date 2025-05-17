import sys
import time
import datetime
import boto3
import json
import requests
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import *
from awsglue.context import GlueContext
from awsglue.job import Job
from requests_auth_aws_sigv4 import AWSSigV4
from botocore.session import Session
import urllib.parse


sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")  

args = getResolvedOptions(sys.argv,['year', 'month', 'cur-database', 'usage-account', 'region', 'prometheus-endpoint', 'work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
usage_account = args['usage_account'].strip()
region = args['region'].strip()
work_bucket = args['work_bucket'].strip()
prometheus_endpoint = args['prometheus_endpoint'].strip()
prometheus_auth = AWSSigV4('aps', region=prometheus_endpoint.split('.')[1], refreshable_credentials=Session().get_credentials()) if prometheus_endpoint.startswith('https://aps-workspaces.') else None

start = datetime.datetime(int(args["year"]),int(args["month"]),1,tzinfo=datetime.timezone.utc)
end = start + datetime.timedelta(days=31)
current_date = start
result_dict = {}
while current_date <= end:
    next_date = current_date + datetime.timedelta(days=10)
    print(f"Get metrics from {current_date} to {next_date}.\n")

    param = {
        "query":'sum(sum_over_time(increase(nginx_ingress_controller_requests[1h])[1d:1h]))by(ingress,region,cluster_name,namespace)*on(ingress)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_ingress_labels[1d]))by(label_app,label_app_kubernetes_io_name,ingress)',
        "start":f'{current_date:%Y-%m-%dT%H:%M:%SZ}',
        "end":f'{next_date:%Y-%m-%dT%H:%M:%SZ}',
        "step":'86400s'
    }
    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?{urllib.parse.urlencode(param)}'
    print(f"Nginx Requests Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=60, auth=prometheus_auth) 
    if response.json()["status"]=="success":
        print(f'Got {len(response.json()["data"]["result"])} items.\n')
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("region", "")
            eks_cluster_name = r["metric"].get("cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", r["metric"].get("label_app_kubernetes_io_name", ""))
            resource_id = f'ingress/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("ingress", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(days=1):%Y-%m-%dT%H:%M:%SZ}'
                if not result_dict.get((year, month, date, usage_account, region, eks_cluster_name, eks_namespace, eks_app, resource_id)):
                    result_dict[(year, month, date, usage_account, region, eks_cluster_name, eks_namespace, eks_app, resource_id)] = {}
                requests_val = result_dict[(year, month, date, usage_account, region, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("requests", 0)
                result_dict[(year, month, date, usage_account, region, eks_cluster_name, eks_namespace, eks_app, resource_id)]["requests"] = requests_val + float(v[1])
                requests_sample = result_dict[(year, month, date, usage_account, region, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("requests_sample", 0)
                result_dict[(year, month, date, usage_account, region, eks_cluster_name, eks_namespace, eks_app, resource_id)]["requests_sample"] = requests_sample + 1
    else:
         print(f'Unexpected Response: {response.json()}')
         
    current_date = next_date

result = []
for k,v in result_dict.items():
    item = {
        "year": k[0],
        "month": k[1],
        "date": k[2],
        "usage_account": k[3],
        "region": k[4],
        "eks_cluster_name": k[5],
        "eks_namespace": k[6],
        "eks_app": k[7],
        "resource_id": k[8],
        "requests": v.get("requests", 0),
        "requests_sample": v.get("requests_sample", 0)
    }
    if item["date"][:7]==f'{args["year"]}-{args["month"]}':
        result.append(item)
print(f'Got {len(result)} items in {args["year"]}-{args["month"]} \n')

if result:
    print(result[:3])
    df_eksmetrics = spark.read.json(sc.parallelize(result)).withColumn("date", to_timestamp("date"))
    (df_eksmetrics.coalesce(1).write
        .mode("overwrite")
        .partitionBy(["usage_account","year","month","region"])
        .option("path", f"s3://{work_bucket}/data/appmetrics_prometheus/res/")
        .saveAsTable(f"{cur_database}.enhanced_cur_appmetrics_prometheus")
    )
    print(f"Job finished. {len(result)} rows was written into table {cur_database}.enhanced_cur_appmetrics_prometheus.\n")
    job.commit()
else:
    print(f"Result is empty.\n")