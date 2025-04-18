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
        "query":'sum(sum_over_time(rate(container_cpu_usage_seconds_total{image!=""}[1h])[1d:1h]))by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,pod,csi_volume_kubernetes_io_nodeid)*on(pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))by(label_app,label_app_kubernetes_io_name,pod)',
        "start":f'{current_date:%Y-%m-%dT%H:%M:%SZ}',
        "end":f'{next_date:%Y-%m-%dT%H:%M:%SZ}',
        "step":'86400s'
    }
    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?{urllib.parse.urlencode(param)}'
    print(f"CPU Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=60, auth=prometheus_auth) 
    if response.json()["status"]=="success":
        print(f'Got {len(response.json()["data"]["result"])} items.\n')
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            if not instance:
                instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("efs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", r["metric"].get("label_app_kubernetes_io_name", ""))
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(days=1):%Y-%m-%dT%H:%M:%SZ}'
                if not result_dict.get((year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)):
                    result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)] = {}
                cpu = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("cpu", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["cpu"] = cpu + float(v[1])
                cpu_samples = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("cpu_samples", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["cpu_samples"] = cpu_samples + 1
    else:
         print(f'Unexpected Response: {response.json()}')
         
    param = {
        "query":'sum(sum_over_time(avg_over_time(container_memory_working_set_bytes{image!=""}[1h])[1d:1h]))by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,csi_volume_kubernetes_io_nodeid,pod)*on(pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))by(label_app,label_app_kubernetes_io_name,pod)',
        "start":f'{current_date:%Y-%m-%dT%H:%M:%SZ}',
        "end":f'{next_date:%Y-%m-%dT%H:%M:%SZ}',
        "step":'86400s'
    }
    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?{urllib.parse.urlencode(param)}'
    print(f"Memory Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=60, auth=prometheus_auth)    
    if response.json()["status"]=="success":
        print(f'Got {len(response.json()["data"]["result"])} items.\n')
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            if not instance:
                instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("efs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", r["metric"].get("label_app_kubernetes_io_name", ""))
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(days=1):%Y-%m-%dT%H:%M:%SZ}'
                if not result_dict.get((year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)):
                    result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)] = {}
                memory = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("memory", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["memory"] = memory + float(v[1])
                memory_samples = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("memory_samples", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["memory_samples"] = memory_samples + 1
    else:
         print(f'Unexpected Response: {response.json()}')                

    param = {
        "query":'avg(avg_over_time(kube_pod_info{host_network="false"}[1d]))by(pod)*on(pod)group_right()sum(sum_over_time(increase(container_network_receive_bytes_total[1h])[1d:1h]))by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,csi_volume_kubernetes_io_nodeid,pod)*on(pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))by(label_app,label_app_kubernetes_io_name,pod)',
        "start":f'{current_date:%Y-%m-%dT%H:%M:%SZ}',
        "end":f'{next_date:%Y-%m-%dT%H:%M:%SZ}',
        "step":'86400s'
    }
    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?{urllib.parse.urlencode(param)}'
    print(f"Network BytesIn Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=60, auth=prometheus_auth)   
    if response.json()["status"]=="success":
        print(f'Got {len(response.json()["data"]["result"])} items.\n')
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            if not instance:
                instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("efs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", r["metric"].get("label_app_kubernetes_io_name", ""))
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(days=1):%Y-%m-%dT%H:%M:%SZ}'
                if not result_dict.get((year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)):
                    result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)] = {}
                networkin = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("networkin", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["networkin"] = networkin + float(v[1])
                networkin_samples = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("networkin_samples", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["networkin_samples"] = networkin_samples + 1
    else:
         print(f'Unexpected Response: {response.json()}')

    param = {
        "query":'sum(sum_over_time(avg_over_time(kube_pod_container_resource_limits{resource="cpu"}[1h])[1d:1h]))by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,pod,csi_volume_kubernetes_io_nodeid)*on(region,cluster,namespace,pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,pod,label_app,label_app_kubernetes_io_name)',
        "start":f'{current_date:%Y-%m-%dT%H:%M:%SZ}',
        "end":f'{next_date:%Y-%m-%dT%H:%M:%SZ}',
        "step":'86400s'
    }
    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?{urllib.parse.urlencode(param)}'
    print(f"Reserved CPU Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=60, auth=prometheus_auth)   
    if response.json()["status"]=="success":
        print(f'Got {len(response.json()["data"]["result"])} items.\n')
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            if not instance:
                instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("efs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", r["metric"].get("label_app_kubernetes_io_name", ""))
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(days=1):%Y-%m-%dT%H:%M:%SZ}'
                if not result_dict.get((year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)):
                    result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)] = {}
                networkin = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("reserved_cpu", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["reserved_cpu"] = networkin + float(v[1])
                networkin_samples = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("reserved_cpu_samples", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["reserved_cpu_samples"] = networkin_samples + 1
    else:
         print(f'Unexpected Response: {response.json()}')

         
    param = {
        "query":'sum(sum_over_time(avg_over_time(kube_pod_container_resource_limits{resource="memory"}[1h])[1d:1h]))by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,pod,csi_volume_kubernetes_io_nodeid)*on(region,cluster,namespace,pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,pod,label_app,label_app_kubernetes_io_name)',
        "start":f'{current_date:%Y-%m-%dT%H:%M:%SZ}',
        "end":f'{next_date:%Y-%m-%dT%H:%M:%SZ}',
        "step":'86400s'
    }
    queryUrl=f'{prometheus_endpoint}/api/v1/query_range?{urllib.parse.urlencode(param)}'
    print(f"Reserved Memory Query URL: {queryUrl}.\n")
    response = requests.get(queryUrl, timeout=60, auth=prometheus_auth)  
    if response.json()["status"]=="success":
        print(f'Got {len(response.json()["data"]["result"])} items.\n')
        for r in response.json()["data"]["result"]:
            year = args["year"]
            month = f'{int(args["month"])}'
            region = r["metric"].get("topology_kubernetes_io_region", "")
            instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("ebs.csi.aws.com", "")
            if not instance:
                instance = json.loads(r["metric"].get("csi_volume_kubernetes_io_nodeid", '{"ebs.csi.aws.com":"","efs.csi.aws.com":""}')).get("efs.csi.aws.com", "")
            eks_cluster_name = r["metric"].get("alpha_eksctl_io_cluster_name", "")
            eks_namespace = r["metric"].get("namespace", "")
            eks_app = r["metric"].get("label_app", r["metric"].get("label_app_kubernetes_io_name", ""))
            resource_id = f'{instance}:pod/{eks_cluster_name}/{eks_namespace}/{r["metric"].get("pod", "")}'
            for v in r["values"]:
                date = f'{datetime.datetime.fromtimestamp(v[0])-datetime.timedelta(days=1):%Y-%m-%dT%H:%M:%SZ}'
                if not result_dict.get((year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)):
                    result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)] = {}
                networkout = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("reserved_mem", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["reserved_mem"] = networkout + float(v[1])
                networkout_samples = result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)].get("reserved_mem_samples", 0)
                result_dict[(year, month, date, usage_account, region, instance, eks_cluster_name, eks_namespace, eks_app, resource_id)]["reserved_mem_samples"] = networkout_samples + 1
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
        "instance": k[5],
        "eks_cluster_name": k[6],
        "eks_namespace": k[7],
        "eks_app": k[8],
        "resource_id": k[9],
        "actual_cpu": v.get("cpu", 0),
        "cpu_samples": v.get("cpu_samples", 0),
        "actual_mem": v.get("memory", 0),
        "memory_samples": v.get("memory_samples", 0),
        "network_in": v.get("networkin", 0),
        "networkin_samples": v.get("networkin_samples", 0),
        "network_out": v.get("networkout", 0),
        "networkout_samples": v.get("networkout_samples", 0)
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
        .option("path", f"s3://{work_bucket}/data/eksmetrics_prometheus/res/")
        .saveAsTable(f"{cur_database}.enhanced_cur_eksmetrics_prometheus")
    )
    print(f"Job finished. {len(result)} rows was written into table {cur_database}.enhanced_cur_eksmetrics_prometheus.\n")
    job.commit()
else:
    print(f"Result is empty.\n")