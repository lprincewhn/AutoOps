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

args = getResolvedOptions(sys.argv,['year', 'month', 'tags-fields', 'cur-database', 'standardize-table', 'work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
cur_table = args['standardize_table'].strip()
work_bucket = args['work_bucket'].strip()
tags_fields = list(map(lambda x:x.strip(), args['tags_fields'].split(',')))

# Load cost data
sql = f'''
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
	eks_cluster_name,
	eks_namespace,
    eks_app,
    sum(usage_amount) as usage_amount,
    sum(vcpus) as vcpus,
    sum(memory_gb) as memory_gb,
    sum(ondemand_cost) as ondemand_cost,
    sum(amortized_cost) as amortized_cost,
    sum(net_amortized_cost) as net_amortized_cost,
    sum(billing_cost) as billing_cost
from {cur_database}.{cur_table}
where year='{args["year"]}' and month='{int(args["month"])}' 
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24
'''
print(sql)
# Replace null value with blank string "" in the original table
df = (spark.sql(sql).fillna(""))
print(f'cost data have {len(df.columns)} columns: {sorted(df.columns)}')
df.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

# Generate the powerset of tags_fields, which used to split the fields into allocated tags and allocating tags
# Cost of blank "allocating tags" will be allocated to records with the same "allocated tags" and date
# The powerset stores the "allocated tags", looks like: [ [], [tag1], [tag2], [tag1, tag2] ]
tags_powerset = []
for i in range(1 << len(tags_fields)):
    tags_powerset.append([tags_fields[j] for j in range(len(tags_fields)) if (i & (1 << j))])

i=0
for allocated in tags_powerset[:-1]:
    i+=1
    allocating = set(tags_fields) - set(allocated)
    print(f'Allocate cost of blank tags {allocating} to records with the same {allocated} and date')
    # Mark the allocated records, the "tag_flag" is true if any allocating tag is not blank
    df = df.withColumn("tag_flag", lit(False))
    for t in allocating:
        df = df.withColumn("tag_flag", col("tag_flag") | (length(col(t))>0))
    # Generate sumtable 
    sumtable = (df
                .withColumn("ondemand_cost_with_tag", when(col("tag_flag"), col("ondemand_cost")).otherwise(0))
                .withColumn("ondemand_cost_without_tag", when(~col("tag_flag"), col("ondemand_cost")).otherwise(0))
                .withColumn("amortized_cost_with_tag", when(col("tag_flag"), col("amortized_cost")).otherwise(0))
                .withColumn("amortized_cost_without_tag", when(~col("tag_flag"), col("amortized_cost")).otherwise(0))
                .withColumn("net_amortized_cost_with_tag", when(col("tag_flag"), col("net_amortized_cost")).otherwise(0))
                .withColumn("net_amortized_cost_without_tag", when(~col("tag_flag"), col("net_amortized_cost")).otherwise(0))
                .withColumn("billing_cost_with_tag", when(col("tag_flag"), col("billing_cost")).otherwise(0))
                .withColumn("billing_cost_without_tag", when(~col("tag_flag"), col("billing_cost")).otherwise(0))
                .groupBy(allocated+["date"])
                .agg({
                    'ondemand_cost_with_tag': 'sum',
                    'ondemand_cost_without_tag': 'sum',
                    'amortized_cost_with_tag': 'sum',
                    'amortized_cost_without_tag': 'sum',
                    'net_amortized_cost_with_tag': 'sum',
                    'net_amortized_cost_without_tag': 'sum',
                    'billing_cost_with_tag': 'sum',
                    'billing_cost_without_tag': 'sum',
                })
    )
    # Join the sumtable and caculate the allocated cost
    df = (df
          .join(sumtable, allocated+["date"], "left")
          .withColumn("allocated_ondemand_cost", when(col("tag_flag"), col("ondemand_cost")+col("ondemand_cost")*col("sum(ondemand_cost_without_tag)")/col("sum(ondemand_cost_with_tag)")).when(col("sum(ondemand_cost_with_tag)")==0, col("ondemand_cost")).otherwise(0))
          .withColumn("allocated_amortized_cost", when(col("tag_flag"), col("amortized_cost")+col("amortized_cost")*col("sum(amortized_cost_without_tag)")/col("sum(amortized_cost_with_tag)")).when(col("sum(amortized_cost_with_tag)")==0, col("amortized_cost")).otherwise(0))
          .withColumn("allocated_net_amortized_cost", when(col("tag_flag"), col("net_amortized_cost")+col("net_amortized_cost")*col("sum(net_amortized_cost_without_tag)")/col("sum(net_amortized_cost_with_tag)")).when(col("sum(net_amortized_cost_with_tag)")==0, col("net_amortized_cost")).otherwise(0))
          .withColumn("allocated_billing_cost", when(col("tag_flag"), col("billing_cost")+col("billing_cost")*col("sum(billing_cost_without_tag)")/col("sum(billing_cost_with_tag)")).when(col("sum(billing_cost_with_tag)")==0, col("billing_cost")).otherwise(0))
    )
    if debug:
        (df.coalesce(1).write
            .mode("overwrite")
            .partitionBy(["usage_account","year","month"])
            .option("path", f"s3://{work_bucket}/data/allocate_untag/{i}/")
            .saveAsTable(f"{cur_database}.enhanced_cur_allocate_untag_{i}")
        )
    # Clean unused columns
    df = (df
          .filter((col("allocated_ondemand_cost")>0)|(col("allocated_amortized_cost")>0)|(col("allocated_billing_cost")>0))
          .withColumn("ondemand_cost",col("allocated_ondemand_cost"))
          .withColumn("amortized_cost",col("allocated_amortized_cost"))
          .withColumn("billing_cost",col("allocated_billing_cost"))
          .drop(
            "tag_flag",
            "sum(ondemand_cost_without_tag)","sum(ondemand_cost_with_tag)",
            "sum(amortized_cost_without_tag)","sum(amortized_cost_with_tag)",
            "sum(net_amortized_cost_without_tag)","sum(net_amortized_cost_with_tag)",
            "sum(billing_cost_without_tag)","sum(billing_cost_with_tag)",
            "allocated_ondemand_cost", "allocated_amortized_cost", "allocated_billing_cost"
        )
    )
    print(f'cost data have {len(df.columns)} columns: {sorted(df.columns)}')
    df.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

print(f"Writing data to s3://{work_bucket}/data/allocate-untag/res/")
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")    
(df.coalesce(1).write
    .mode("overwrite")
    .partitionBy(["usage_account","year","month"])
    .option("path", f"s3://{work_bucket}/data/allocate-untag/res/")
    .saveAsTable(f"{cur_database}.enhanced_cur_allocate_untag")
)
print(f"Job finished.")
job.commit()