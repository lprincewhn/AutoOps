import sys
import datetime
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

# Example Input:
# args = {
#     "year": "2025",
#     "month": "03",
#     "cur_database": "athenacurcfn_c_u_r_athena",
#     "eksmetrics_table": "enhanced_cur_eksmetrics_prometheus",
#     "standardize_table": "enhanced_cur_standardize",
#     "work_bucket": "cur-597377428377",
#     "verbose": "0"
# }
args = getResolvedOptions(sys.argv,['year', 'month', 'cur-database', 'eksmetrics-table', 'standardize-table', 'work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
work_bucket = args['work_bucket'].strip()
eksmetrics_table = args['eksmetrics_table'].strip() 
standardize_table = args['standardize_table'].strip()
year=int(args["year"])
month=int(args["month"])

# Load EKS metrics data
eks_sql = f'''
select
    year,
    month,
    region,
    date(date) as date,
    usage_account,
    resource_id,
    instance,
    eks_cluster_name,
    eks_namespace,
    eks_app,
    sum(actual_cpu) as actual_cpu,
    sum(actual_mem) as actual_mem,
    sum(network_in) as network_in,
    sum(network_out) as network_out,
    sum(0) as reserved_cpu,
    sum(0) as reserved_mem,
    '1' as eks_flag
from {cur_database}.{eksmetrics_table}
where year='{year}' and month='{month}' 
group by 1,2,3,4,5,6,7,8,9,10
'''
print(f"Load EKS metric with SQL: {eks_sql}\n")
df_eks = (spark.sql(eks_sql).fillna("")
            .withColumn("cpu_usage", greatest(col("actual_cpu"), col("reserved_cpu")))
            .withColumn("mem_usage", greatest(col("actual_mem"), col("reserved_mem")))
            .withColumn("network_usage", col("network_out")+col("network_in"))
         )
print(f'EKS metrics data have {len(df_eks.columns)} columns: {sorted(df_eks.columns)}\n')
df_eks.describe(['eks_flag']).show(vertical=True)

# Load cost data
cost_sql = f'''
select
	year,
	month,
	date,
	charge_type,
	payer_account,
	usage_account,
	billing_entity,
	service, 
	product,
	region,
	location,
	instance_type,
	instance_family,
	database_engine,
	volume_type,
	usage_type,
	description,
	resource_id,
	emr_job_flow_id,
	project,
	name,
	sum(usage_amount) as usage_amount,
	sum(vcpus) as vcpus,
	sum(gpus) as gpus,
	sum(memory_gb) as memory_gb, 
	sum(ondemand_cost) as ondemand_cost,
	sum(amortized_cost) as amortized_cost,
	sum(net_amortized_cost) as net_amortized_cost,
	sum(billing_cost) as billing_cost
from {cur_database}.{standardize_table}
where year='{year}' and month='{month}' 
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21
'''
print(f"Load cost with SQL: {cost_sql}\n")	
df_cost = (spark.sql(cost_sql).fillna(""))
print(f'Cost data have {len(df_cost.columns)} columns: {sorted(df_cost.columns)}\n')
df_cost.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

# Update column eks_flag to mark items to be allocated: 0-Non EKS; 1-EKS Instance; 2-EKS DataTransfer.
df_cost_eks_flag = (df_cost
    .join(
        df_eks
            .withColumn("resource_id",col("instance"))
            .drop("instance")
            .groupBy("year","month","usage_account","date", "region", "resource_id")
            .agg(sum("eks_flag")), 
        ["year","month","usage_account","date", "region", "resource_id"], 
        "left")
    .withColumn("eks_flag", 
        when((col("sum(eks_flag)")>0) & (col("usage_type").contains("BoxUsage") | col("usage_type").contains("SpotUsage")), 1)
        .when((col("sum(eks_flag)")>0) & (col("usage_type").contains("DataTransfer")), 2)
        .otherwise(0)
    )
)
print(f'Cost data with eks flag have {len(df_cost_eks_flag.columns)} columns: {sorted(df_cost_eks_flag.columns)}\n')
df_cost_eks_flag.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost','eks_flag']).show(vertical=True)
df_cost_eks_flag.groupBy("eks_flag").agg(count(lit(1)), sum("vcpus"), sum("memory_gb"), sum("ondemand_cost"), sum("amortized_cost"), sum("net_amortized_cost"), sum("billing_cost"), sum("eks_flag")).show(vertical=True)

if debug:
    (df_cost_eks_flag.coalesce(1).write
        .mode("overwrite")
        .partitionBy(["usage_account","year","month"])
        .option("path", f"s3://{work_bucket}/data/enhanced_cur_allocate_eks_1/")
        .saveAsTable(f"{cur_database}.enhanced_cur_allocate_eks_1")
    )

# Generate metrics sumtable 
sumtable = (df_eks
                .groupBy(["year","month","usage_account","date", "region", "instance"])
                .agg(sum("cpu_usage"), sum("mem_usage"), sum("network_usage"))
)
print(f'EKS metric grouped by instance and date have {len(sumtable.columns)} columns: {sorted(sumtable.columns)}\n')
sumtable.describe(['sum(cpu_usage)', 'sum(mem_usage)', 'sum(network_usage)']).show(vertical=True)

# Join the sumtable and eks cost items to caculate the allocated cost of EC2 instance
df_eks_ec2 = (df_eks
        .join(sumtable, ["year", "month", "usage_account", "date", "region", "instance"], "left")
        .join(
            df_cost_eks_flag
              .filter(col('eks_flag')==1)
              .withColumn("instance",col("resource_id"))
              .withColumn("cpu_cost_ratio", col("vcpus")*9/(col("vcpus")*9+col("memory_gb")))
              .drop("resource_id", "eks_flag"), 
            ["year", "month", "usage_account", "date", "region", "instance"], 
            "left")
        .withColumn("vcpus", col("vcpus")*col("cpu_usage")/col("sum(cpu_usage)"))
        .withColumn("memory_gb", col("memory_gb")*col("mem_usage")/col("sum(mem_usage)"))
        .withColumn("usage_amount", col("usage_amount")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("usage_amount")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
        .withColumn("ondemand_cost", col("ondemand_cost")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("ondemand_cost")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
        .withColumn("amortized_cost", col("amortized_cost")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("amortized_cost")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
        .withColumn("net_amortized_cost", col("net_amortized_cost")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("net_amortized_cost")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
        .withColumn("billing_cost", col("billing_cost")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("billing_cost")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
)

print(f'EKS metric with allocated ec2 instance cost have {len(df_eks_ec2.columns)} columns: {sorted(df_eks_ec2.columns)}\n')
df_eks_ec2.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

if debug:
    (df_eks_ec2.coalesce(1).write
        .mode("overwrite")
        .partitionBy(["usage_account","year","month"])
        .option("path", f"s3://{work_bucket}/data/enhanced_cur_allocate_eks_2/")
        .saveAsTable(f"{cur_database}.enhanced_cur_allocate_eks_2")
    )
    
# Join the sumtable and eks cost items to caculate the allocated cost of EC2 datatransfer
df_eks_dt = (df_eks
        .join(sumtable, ["year", "month", "usage_account", "date", "region", "instance"], "left")
        .join(
            df_cost_eks_flag
              .filter(col('eks_flag')==2)
              .withColumn("instance",col("resource_id"))
              .withColumn("cpu_cost_ratio", col("vcpus")*9/(col("vcpus")*9+col("memory_gb")))
              .drop("resource_id", "eks_flag"), 
            ["year", "month", "usage_account", "date", "region", "instance"], 
            "left")
        .withColumn("vcpus", lit(0))
        .withColumn("memory_gb", lit(0))
        .withColumn("usage_amount", col("usage_amount")*col("network_usage")/col("sum(network_usage)"))
        .withColumn("ondemand_cost", col("ondemand_cost")*col("network_usage")/col("sum(network_usage)"))
        .withColumn("amortized_cost", col("amortized_cost")*col("network_usage")/col("sum(network_usage)"))
        .withColumn("net_amortized_cost", col("net_amortized_cost")*col("network_usage")/col("sum(network_usage)"))
        .withColumn("billing_cost", col("billing_cost")*col("network_usage")/col("sum(network_usage)"))
)

print(f'EKS metric with allocated ec2 datatransfer cost have {len(df_eks_dt.columns)} columns: {sorted(df_eks_dt.columns)}\n')
df_eks_dt.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

if debug:
    (df_eks_dt.coalesce(1).write
        .mode("overwrite")
        .partitionBy(["usage_account","year","month"])
        .option("path", f"s3://{work_bucket}/data/enhanced_cur_allocate_eks_3/")
        .saveAsTable(f"{cur_database}.enhanced_cur_allocate_eks_3")
    )
    
# Clean unused columns and merge back to cost data.
df = (df_eks_ec2
        .drop("instance","actual_cpu","actual_mem","reserved_cpu","reserved_mem","eks_flag","sum(eks_flag)","cpu_usage","sum(cpu_usage)","mem_usage","sum(mem_usage)", "network_in", "network_out", "network_usage","sum(network_usage)", "cpu_cost_ratio")
        .unionByName(df_eks_dt
            .drop("instance","actual_cpu","actual_mem","reserved_cpu","reserved_mem","eks_flag","sum(eks_flag)","cpu_usage","sum(cpu_usage)","mem_usage","sum(mem_usage)", "network_in", "network_out", "network_usage","sum(network_usage)", "cpu_cost_ratio")
            .drop("sum(eks_flag)","eks_flag")
        )        
        .unionByName(df_cost_eks_flag
            .filter(col("eks_flag")==0)
            .drop("sum(eks_flag)","eks_flag")
            .withColumn("eks_cluster_name", lit(""))
            .withColumn("eks_namespace", lit(""))
            .withColumn("eks_app", lit(""))
        )
)
print(f'Cost data with allocated eks cost have {len(df.columns)} columns: {sorted(df.columns)}\n')
df.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

print(f"Writing data to s3://{work_bucket}/data/allocate-eks/res/")
(df.coalesce(1).write
    .mode("overwrite")
    .partitionBy(["usage_account","year","month"])
    .option("path", f"s3://{work_bucket}/data/allocate-eks/")
    .saveAsTable(f"{cur_database}.enhanced_cur_allocate_eks")
)
print(f"Job finished.")
job.commit()