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

args = getResolvedOptions(sys.argv,['year', 'month', 'tags-fields', 'cur-database','work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
work_bucket = args['work_bucket'].strip()
tags_fields = list(map(lambda x:x.strip(), args['tags_fields'].split(',')))
eksmetrics_table = 'enhanced_cur_eksmetrics'
standardize_table = 'enhanced_cur_standardize'

# Load EKS metrics data
eks_sql = f'''
select
    year,
    month,
    region,
    usage_date,
    usage_account,
    resource_id,
    instance,
    {",".join(tags_fields)},
    sum(actual_cpu) as actual_cpu,
    sum(actual_mem) as actual_mem,
    sum(reserved_cpu) as reserved_cpu,
    sum(reserved_mem) as reserved_mem,
    sum(actual_cpu_cnt) as samples,
    '1' as eks_flag
from {cur_database}.{eksmetrics_table}
where year='{args["year"]}' and month='{args["month"]}' 
group by {",".join(map(lambda x:str(x), range(1,len(tags_fields)+8)))}
'''
print(eks_sql)
df_eks = (spark.sql(eks_sql).fillna("")
            .withColumn("cpu_usage", greatest(col("actual_cpu"), col("reserved_cpu")))
            .withColumn("mem_usage", greatest(col("actual_mem"), col("reserved_mem")))
         )
print(f'eks metrics data have {len(df_eks.columns)} columns: {sorted(df_eks.columns)}')
df_eks.describe(['samples']).show(vertical=True)

# Load cost data
cost_sql = f'''
select
    year,
    month,
    charge_type,
    billing_entity,
    service, 
    region,
    instance_type,
    instance_family,
    database_engine,
    usage_type,
    usage_date,
    usage_account,
    resource_id,
    {",".join(tags_fields)},
    sum(usage_amount) as usage_amount,
    sum(vcpus) as vcpus,
    sum(memory_gb) as memory_gb,
    sum(ondemand_cost) as ondemand_cost,
    sum(amortized_cost) as amortized_cost,
    sum(net_amortized_cost) as net_amortized_cost,
    sum(billing_cost) as billing_cost
from {cur_database}.{standardize_table}
where year='{args["year"]}' and month='{args["month"]}' 
group by {",".join(map(lambda x:str(x), range(1,len(tags_fields)+14)))}
'''
print(cost_sql)
df_cost = (spark.sql(cost_sql).fillna(""))
print(f'cost data have {len(df_cost.columns)} columns: {sorted(df_cost.columns)}')
df_cost.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

# Update column eks_flag to mark items to be allocated
df_cost_eks_flag = (df_cost
    .join(df_eks.withColumn("resource_id",col("instance")).drop("instance").groupBy("year","month","usage_account","usage_date", "region", "resource_id").agg(sum("eks_flag")), ["year","month","usage_account","usage_date", "region", "resource_id"], "left")
    .withColumn("eks_flag", when((col("sum(eks_flag)")>0) & (col("usage_type").contains("BoxUsage") | col("usage_type").contains("SpotUsage")), 1).otherwise(0))
)
print(f'cost data with eks flag have {len(df_cost_eks_flag.columns)} columns: {sorted(df_cost_eks_flag.columns)}')
df_cost_eks_flag.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost','eks_flag']).show(vertical=True)
df_cost_eks_flag.groupBy("eks_flag").agg(count(lit(1)), sum("vcpus"), sum("memory_gb"), sum("ondemand_cost"), sum("amortized_cost"), sum("net_amortized_cost"), sum("billing_cost"), sum("eks_flag")).show(vertical=True)

# Generate metrics sumtable 
sumtable = (df_eks
            .groupBy(["year","month","usage_account","usage_date", "region", "instance"])
            .agg(sum("cpu_usage"), sum("mem_usage"))
)
print(f'esk metric data grouped by instance and usage_date have {len(sumtable.columns)} columns: {sorted(sumtable.columns)}')
sumtable.describe(['sum(cpu_usage)', 'sum(mem_usage)']).show(vertical=True)

# Join the sumtable and eks cost items to caculate the allocated cost
df = (df_eks
      .join(sumtable, ["year","month","usage_account","usage_date", "region", "instance"], "left")
      .join(df_cost_eks_flag.filter(col('eks_flag')==1).withColumn("instance",col("resource_id")).withColumn("cpu_cost_ratio", col("vcpus")*9/(col("vcpus")*9+col("memory_gb"))).drop("resource_id", "name", "eks_flag"), ["year","month","usage_account","usage_date", "region", "instance"], "left")
      .withColumn("vcpus", col("vcpus")*col("cpu_usage")/col("sum(cpu_usage)"))
      .withColumn("memory_gb", col("memory_gb")*col("mem_usage")/col("sum(mem_usage)"))
      .withColumn("usage_amount", col("usage_amount")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("usage_amount")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
      .withColumn("ondemand_cost", col("ondemand_cost")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("ondemand_cost")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
      .withColumn("amortized_cost", col("amortized_cost")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("amortized_cost")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
      .withColumn("net_amortized_cost", col("net_amortized_cost")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("net_amortized_cost")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
      .withColumn("billing_cost", col("billing_cost")*col("cpu_cost_ratio")*col("cpu_usage")/col("sum(cpu_usage)")+col("billing_cost")*(1-col("cpu_cost_ratio"))*col("mem_usage")/col("sum(mem_usage)"))
)

print(f'eks metric data with allocated cost have {len(df.columns)} columns: {sorted(df.columns)}')
df.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

if debug:
    (df.coalesce(1).write
        .mode("overwrite")
        .partitionBy(["usage_account","year","month"])
        .option("path", f"s3://{work_bucket}/data/enhanced_cur_allocate_eks_1/")
        .saveAsTable(f"{cur_database}.enhanced_cur_allocate_eks_1")
    )
    
# Clean unused columns and merge back to cost data.
df = (df
      .drop("instance","actual_cpu","actual_mem","reserved_cpu","reserved_mem","samples","eks_flag","sum(eks_flag)","cpu_usage","sum(cpu_usage)","mem_usage","sum(mem_usage)", "cpu_cost_ratio")
      .unionByName(df_cost_eks_flag.filter(col("eks_flag")!=1).drop("sum(eks_flag)","eks_flag"))
)
print(f'cost data with allocated eks cost have {len(df.columns)} columns: {sorted(df.columns)}')
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