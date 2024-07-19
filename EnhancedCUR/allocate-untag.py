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

args = getResolvedOptions(sys.argv,['month', 'tags-fields', 'cur-database', 'cur-table','work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
cur_table = args['cur_table'].strip()
work_bucket = args['work_bucket'].strip()
yearmonth = datetime.datetime.strptime(args["month"], '%Y-%m').date()
tags_fields = list(map(lambda x:x.strip(), args['tags_fields'].split(',')))
select_fields = ",".join(tags_fields)
groupby = ",".join(map(lambda x:str(x), range(1,len(tags_fields)+10)))

sql = f'''
select
    usage_account,
    year,
    month,
    usage_date,
    service, 
    region,
    resource_id,
    charge_type,
    usage_type,
    {select_fields},
    sum(ondemand_cost) as ondemand_cost,
    sum(amortized_cost) as amortized_cost,
    sum(billing_cost) as billing_cost
from {cur_database}.{cur_table}
where year='{yearmonth.year}' and month='{yearmonth.month:02d}' 
group by {groupby}
'''
print(sql)

# Replace null value with blank string "" in the original table
df = (spark.sql(sql).fillna(""))

sum = df.agg({"ondemand_cost": "sum", "amortized_cost": "sum", "billing_cost": "sum"}).collect()
print(f"rows: {df.count()}, ondemand_cost: {sum[0][0]}, amortized_cost: {sum[0][1]}, billing_cost: {sum[0][2]}")

# Generate the powerset of tags_fields, which used to split the fields into allocated tags and allocating tags
# Cost of blank "allocating tags" will be allocated to records with the same "allocated tags" and usage_date
# The powerset stores the "allocated tags", looks like: [ [], [tag1], [tag2], [tag1, tag2] ]
tags_powerset = []
for i in range(1 << len(tags_fields)):
    tags_powerset.append([tags_fields[j] for j in range(len(tags_fields)) if (i & (1 << j))])

i=0
for allocated in tags_powerset[:-1]:
    i+=1
    allocating = set(tags_fields) - set(allocated)
    print(f'Allocate cost of blank tags {allocating} to records with the same {allocated} and usage_date')
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
                .withColumn("billing_cost_with_tag", when(col("tag_flag"), col("billing_cost")).otherwise(0))
                .withColumn("billing_cost_without_tag", when(~col("tag_flag"), col("billing_cost")).otherwise(0))
                .groupBy(allocated+["usage_date"])
                .agg({
                    'ondemand_cost_with_tag': 'sum',
                    'ondemand_cost_without_tag': 'sum',
                    'amortized_cost_with_tag': 'sum',
                    'amortized_cost_without_tag': 'sum',
                    'billing_cost_with_tag': 'sum',
                    'billing_cost_without_tag': 'sum',
                })
    )
    # Join the sumtable and caculate the allocated cost
    df = (df
          .join(sumtable, allocated+["usage_date"], "left")
          .withColumn("allocated_ondemand_cost", when(col("tag_flag"), col("ondemand_cost")+col("ondemand_cost")*col("sum(ondemand_cost_without_tag)")/col("sum(ondemand_cost_with_tag)")).when(col("sum(ondemand_cost_with_tag)")==0, col("ondemand_cost")).otherwise(0))
          .withColumn("allocated_amortized_cost", when(col("tag_flag"), col("amortized_cost")+col("amortized_cost")*col("sum(amortized_cost_without_tag)")/col("sum(amortized_cost_with_tag)")).when(col("sum(amortized_cost_with_tag)")==0, col("amortized_cost")).otherwise(0))
          .withColumn("allocated_billing_cost", when(col("tag_flag"), col("billing_cost")+col("billing_cost")*col("sum(billing_cost_without_tag)")/col("sum(billing_cost_with_tag)")).when(col("sum(billing_cost_with_tag)")==0, col("billing_cost")).otherwise(0))
    )
    if debug:
        (df.coalesce(1).write
            .mode("overwrite")
            .partitionBy(["usage_account","year","month"])
            .option("path", f"s3://{work_bucket}/data/{cur_table}_allocate_untag_{i}/")
            .saveAsTable(f"{cur_database}.{cur_table}_allocate_untag_{i}")
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
            "sum(billing_cost_without_tag)","sum(billing_cost_with_tag)",
            "allocated_ondemand_cost", "allocated_amortized_cost", "allocated_billing_cost"
        )
    )
    sum = df.agg({"ondemand_cost": "sum", "amortized_cost": "sum", "billing_cost": "sum"}).collect()
    print(f"rows: {df.count()}, ondemand_cost: {sum[0][0]}, amortized_cost: {sum[0][1]}, billing_cost: {sum[0][2]}")

print(f"Writing data to s3://{work_bucket}/data/allocate-untag/res/")
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")    
(df.coalesce(1).write
    .mode("overwrite")
    .partitionBy(["usage_account","year","month"])
    .option("path", f"s3://{work_bucket}/data/{cur_table}_allocate_untag_res/")
    .saveAsTable(f"{cur_database}.{cur_table}_allocate_untag_res")
)
print(f"Job finished.")