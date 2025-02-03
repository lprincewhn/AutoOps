import sys
import time
import datetime
import boto3
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

args = getResolvedOptions(sys.argv,['year', 'month', 'cur-database', 'cur-table','work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
cur_table = args['cur_table'].strip()
work_bucket = args['work_bucket'].strip()

sql = f'''
select
	year,
	month,
	date(line_item_usage_start_date) as date,
	line_item_line_item_type as charge_type,
	bill_payer_account_id as payer_account,
	line_item_usage_account_id as usage_account,
	case when bill_billing_entity='AWS' then 'AWS' else line_item_legal_entity end as billing_entity,
	case
		when length(split_line_item_parent_resource_id)>0 then 'AmazonEC2' 
		when length(product_servicecode)>0 then product_servicecode 
		when bill_billing_entity='AWS' then line_item_product_code 
		else product_product_name end as service, 
	case
		when length(split_line_item_parent_resource_id)>0 then 'AmazonEC2'  
		when bill_billing_entity='AWS' then line_item_product_code 
		else product_product_name end as product,
	product_region as region,
	product_location as location,
	product_instance_type as instance_type,
	regexp_extract(product_instance_type, '([a-z][1-9].{{0,1}})\.', 1) as instance_family,
	product_database_engine as database_engine,
	product_volume_type as volume_type,
	line_item_usage_type as usage_type,
	line_item_line_item_description as description,
	line_item_resource_id as resource_id,
	resource_tags_aws_elasticmapreduce_job_flow_id as emr_job_flow_id,
	resource_tags_user_project as project,
	resource_tags_user_name as name,
	sum(line_item_usage_amount) as usage_amount,
	sum(case when line_item_line_item_type like '%Usage' and line_item_usage_type not like '%EBSOptimized%' then cast(NULLIF(TRIM(product_vcpu), '') as decimal)*line_item_usage_amount else 0 end) as vcpus,
	sum(case when line_item_line_item_type like '%Usage' and line_item_usage_type not like '%EBSOptimized%' then cast(NULLIF(NULLIF(TRIM(product_gpu), ''), 'N/A') as decimal)*line_item_usage_amount else 0 end) as gcpus,
	sum(case when line_item_line_item_type like '%Usage' and line_item_usage_type not like '%EBSOptimized%' then COALESCE(cast(NULLIF(regexp_extract(product_memory, '([\.|0-9]{{1,6}}) GiB', 1), '') as decimal), cast(NULLIF(TRIM(product_memory_gib), '') as decimal))*line_item_usage_amount else 0 end) as memory_gb,
	sum(case
	    when line_item_line_item_type like '%Discount' then 0
	    when line_item_line_item_type='SavingsPlanNegation' then 0
	    when line_item_line_item_type='SavingsPlanUpfrontFee' then 0
	    when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0
	    when line_item_line_item_type='DiscountedUsage' then pricing_public_on_demand_cost
	    when line_item_line_item_type='Usage' then line_item_unblended_cost
	    when line_item_line_item_type='SavingsPlanCoveredUsage' then pricing_public_on_demand_cost
	    when line_item_line_item_type='RIFee' then reservation_unused_amortized_upfront_fee_for_billing_period+reservation_unused_recurring_fee
	    when line_item_line_item_type='SavingsPlanRecurringFee' then savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment
	    else line_item_unblended_cost end) as ondemand_cost,
	sum(case
	    when line_item_line_item_type like '%Discount' then 0
	    when line_item_line_item_type='SavingsPlanNegation' then 0
	    when line_item_line_item_type='SavingsPlanUpfrontFee' then 0
	    when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0
	    when line_item_line_item_type='DiscountedUsage' then reservation_effective_cost
	    when line_item_line_item_type='Usage' then line_item_unblended_cost
	    when line_item_line_item_type='SavingsPlanCoveredUsage' then savings_plan_savings_plan_effective_cost
	    when line_item_line_item_type='RIFee' then reservation_unused_amortized_upfront_fee_for_billing_period+reservation_unused_recurring_fee
	    when line_item_line_item_type='SavingsPlanRecurringFee' then savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment
	    else line_item_unblended_cost end) as amortized_cost,
	sum(case
	    when line_item_line_item_type like '%Discount' then 0
	    when line_item_line_item_type='SavingsPlanNegation' then 0
	    when line_item_line_item_type='SavingsPlanUpfrontFee' then 0
	    when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0
	    when line_item_line_item_type='DiscountedUsage' then reservation_net_effective_cost
	    when line_item_line_item_type='Usage' then line_item_net_unblended_cost
	    when line_item_line_item_type='SavingsPlanCoveredUsage' then savings_plan_net_savings_plan_effective_cost
	    when line_item_line_item_type='RIFee' then reservation_net_unused_amortized_upfront_fee_for_billing_period+reservation_net_unused_recurring_fee
	    when line_item_line_item_type='SavingsPlanRecurringFee' then (savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment)*(case when isnan(line_item_net_unblended_cost/line_item_unblended_cost) then savings_plan_net_amortized_upfront_commitment_for_billing_period/savings_plan_amortized_upfront_commitment_for_billing_period else line_item_net_unblended_cost/line_item_unblended_cost end)
	    else line_item_net_unblended_cost end) as net_amortized_cost,
	sum(line_item_unblended_cost) as billing_cost
from {cur_database}.{cur_table}
where year='{int(args["year"])}' and month='{int(args["month"])}' 
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21
'''
print(sql)

# Replace null value with blank string "" in the original table
df = spark.sql(sql).fillna("")
df.describe(['vcpus', 'memory_gb', 'ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

print(f"Writing data to s3://{work_bucket}/data/standardize/res/")
(df.coalesce(1).write
    .mode("overwrite")
    .partitionBy(["usage_account","year","month"])
    .option("path", f"s3://{work_bucket}/data/standardize/res/")
    .saveAsTable(f"{cur_database}.enhanced_cur_standardize")
)

print(f"Job finished.")
job.commit()