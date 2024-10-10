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

eks_sql = f'''
select
    year,
    month,
    region,
    usage_type,
    usage_date,
    usage_account,
    resource_id,
    instance,
    {",".join(tags_fields)},
    sum(usage_amount) as usage_amount
from {cur_database}.{eksmetrics_table}
where year='{args["year"]}' and month='{args["month"]}' 
group by {",".join(map(lambda x:str(x), range(1,len(tags_fields)+9)))}
'''
print(eks_sql)
# Replace null value with blank string "" in the original table
df_eks = (spark.sql(eks_sql).fillna(""))
stat = df_eks.agg({"usage_amount": "sum"}).collect()
print(f"rows: {df_eks.count()}, usage_amount: {stat[0][0]}")

cost_sql = f'''
select
    year,
    month,
    charge_type,
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
group by {",".join(map(lambda x:str(x), range(1,len(tags_fields)+13)))}
'''
print(cost_sql)
# Replace null value with blank string "" in the original table
df_cost = (spark.sql(cost_sql).fillna(""))
stat = df_cost.agg({"vcpus": "sum", "memory_gb": "sum", "ondemand_cost": "sum", "amortized_cost": "sum", "net_amortized_cost": "sum", "billing_cost": "sum"}).collect()
print(f"rows: {df_cost.count()}, vcpus: {stat[0][0]}, memory_gb: {stat[0][1]}, ondemand_cost: {stat[0][2]}, amortized_cost: {stat[0][3]}, net_amortized_cost: {stat[0][4]}, billing_cost: {stat[0][5]}")

df_cost.filter(col('usage_type').contains('BoxUsage') | col('usage_type').contains('SpotUsage')).agg({'resource_id':'count','amortized_cost':'sum'})

# Generate sumtable 
sumtable = (df_eks
            .groupBy(["year","month","usage_account","usage_date", "usage_type", "region", "instance"])
            .agg({
                'usage_amount': 'sum',
            })
)

# Join the sumtable and caculate the allocated cost
df = (df_eks
      .join(sumtable, ["year","month","usage_account","usage_date", "usage_type", "region", "instance"], "left")
      .join(df_cost.withColumn("instance",col("resource_id")).drop("resource_id","usage_amount","usage_type","name").filter(col('usage_type').contains('BoxUsage') | col('usage_type').contains('SpotUsage')), ["year","month","usage_account","usage_date", "region", "instance"], "left")
      .withColumn("allocated_amortized_cost", when(col("usage_type")=="Pod-Memory", col("amortized_cost")*0.1*col("usage_amount")/col("sum(usage_amount)")).when(col("usage_type")=="Pod-vCPU", col("amortized_cost")*0.9*col("usage_amount")/col("sum(usage_amount)")).otherwise(0))
)
df.agg({'resource_id':'count','allocated_amortized_cost':'sum'})

if debug:
    (df.coalesce(1).write
        .mode("overwrite")
        .partitionBy(["usage_account","year","month"])
        .option("path", f"s3://{work_bucket}/data/enhanced_cur_allocate_eks_1/")
        .saveAsTable(f"{cur_database}.enhanced_cur_allocate_eks_1")
    )
# Clean unused columns
# df = (df
#       .drop(
#         "instance"
#     )
# )
# print(f"Writing data to s3://{work_bucket}/data/allocate-untag/res/")
# (df.coalesce(1).write
#     .mode("overwrite")
#     .partitionBy(["usage_account","year","month"])
#     .option("path", f"s3://{work_bucket}/data/{cur_table}_allocate_untag_res/")
#     .saveAsTable(f"{cur_database}.{cur_table}_allocate_untag_res")
# )
print(f"Job finished.")
job.commit()