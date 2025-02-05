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
        

start = datetime.datetime(int(args["year"]),int(args["month"]),1,tzinfo=datetime.timezone.utc)
end = start + datetime.timedelta(days=31)
current_date = start
result_dict = {}
while current_date <= end:
    next_date = current_date + datetime.timedelta(days=10)
    print(f"Get metrics from {current_date} to {next_date}.\n")
    
    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?query=sum(rate(container_cpu_usage_seconds_total{{image!=""}}[1h]))by(topology_kubernetes_io_region,csi_volume_kubernetes_io_nodeid,alpha_eksctl_io_cluster_name,namespace,pod)*100*on(pod)group_left(label_app)kube_pod_labels&start={current_date:%Y-%m-%dT%H:%M:%SZ}&end={next_date:%Y-%m-%dT%H:%M:%SZ}&step=3600s'
    print(f"CPU Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=5)
    if response.json()["status"]=="success":
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", "")
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(hours=1):%Y-%m-%dT%H:%M:%SZ}'
                if not result_dict.get((year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)):
                    result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)] = {}
                cpu = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("cpu", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["cpu"] = cpu + float(v[1])

    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?sum(container_memory_working_set_bytes{{image!=""}})by(topology_kubernetes_io_region, csi_volume_kubernetes_io_nodeid, alpha_eksctl_io_cluster_name, namespace, pod)*on(pod)group_left(label_app)kube_pod_labels&start={current_date:%Y-%m-%dT%H:%M:%SZ}&end={next_date:%Y-%m-%dT%H:%M:%SZ}&step=3600s'
    print(f"Memory Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=5)    
    if response.json()["status"]=="success":
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", "")
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(hours=1):%Y-%m-%dT%H:%M:%SZ}'
                memory = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("memory", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["memory"] = memory + float(v[1])

    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?query=avg(kube_pod_info{{host_network="false"}})by(pod)*on(pod)group_right()sum(increase(container_network_receive_bytes_total[1h]))by(topology_kubernetes_io_region,csi_volume_kubernetes_io_nodeid,alpha_eksctl_io_cluster_name,namespace,pod)*on(pod)group_left(label_app)avg(kube_pod_labels)by(pod, label_app)&start={current_date:%Y-%m-%dT%H:%M:%SZ}&end={next_date:%Y-%m-%dT%H:%M:%SZ}&step=3600s'
    print(f"Network BytesIn Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=5)    
    if response.json()["status"]=="success":
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", "")
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(hours=1):%Y-%m-%dT%H:%M:%SZ}'
                networkin = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("networkin", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["networkin"] = networkin + float(v[1])

    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?query=avg(kube_pod_info{{host_network="false"}})by(pod)*on(pod)group_right()sum(increase(container_network_transmit_bytes_total[1h]))by(topology_kubernetes_io_region,csi_volume_kubernetes_io_nodeid,alpha_eksctl_io_cluster_name,namespace,pod)*on(pod)group_left(label_app)avg(kube_pod_labels)by(pod, label_app)&start={current_date:%Y-%m-%dT%H:%M:%SZ}&end={next_date:%Y-%m-%dT%H:%M:%SZ}&step=3600s'
    print(f"Network BytesOut Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=5)    
    if response.json()["status"]=="success":
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", "")
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(hours=1):%Y-%m-%dT%H:%M:%SZ}'
                networkout = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("networkout", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["networkin"] = networkout + float(v[1])
                
    current_date = next_date

result = []
for k,v in result_dict.items():
    item = {
        "year": k[0],
        "month": k[1],
        "date": k[2],
        "usage_account": k[3],
        "region": k[4],
        "instance": k[5],
        "eks_cluster_name": k[6],
        "eks_namespace": k[7],
        "eks_app": k[8],
        "resource_id": k[9],
        "actual_cpu": v.get("cpu", 0),
        "actual_mem": v.get("memory", 0),
        "network_in": v.get("networkin", 0),
        "network_out": v.get("networkout", 0)
    }
    if item["date"][:7]==f'{args["year"]}-{args["month"]}':
        result.append(item)
print(f"Got {len(result)} items.\n")
print(result[0])
    
if result:
    print(result[:3])
    df_eksmetrics = spark.read.json(sc.parallelize(result)).withColumn("date", to_timestamp("date"))
    (df_eksmetrics.coalesce(1).write
        .mode("overwrite")
        .partitionBy(["usage_account","year","month","region"])
        .option("path", f"s3://{work_bucket}/data/eksmetrics_prometheus/res/")
        .saveAsTable(f"{cur_database}.enhanced_cur_eksmetrics_prometheus")
    )
    print(f"Job finished. {len(result)} rows was written into table {cur_database}.enhanced_cur_eksmetrics_prometheus.\n")
    job.commit()
else:
    print(f"Result is empty.\n")