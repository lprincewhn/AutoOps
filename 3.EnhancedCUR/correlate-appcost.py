# Only allocate EKS EC2 cost
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
args = getResolvedOptions(sys.argv,['year', 'month', 'cur-database', 'appmetrics-table', 'cost-table', 'work-bucket', 'verbose'])
print(f"args: {args}")
debug = int(args["verbose"])
cur_database = args['cur_database'].strip()
work_bucket = args['work_bucket'].strip()
appmetrics_table = args['appmetrics_table'].strip() 
cost_table = args['cost_table'].strip() 

# Load APP metrics data
app_sql = f'''
select 
    year, 
    month, 
    usage_account, 
    date, 
    eks_app, 
    eks_cluster_name, 
    eks_namespace, 
    region,
    sum(requests) AS requests
from {cur_database}.{appmetrics_table}
where year='{int(args["year"])}' and month='{int(args["month"])}' 
group by 1,2,3,4,5,6,7,8
'''
print(f"Load APP metric with SQL: {app_sql}\n")
df_app = (spark.sql(app_sql).fillna(""))
print(f'APP metrics data have {len(df_app.columns)} columns: {sorted(df_app.columns)}\n')
df_app.describe(['requests']).show(vertical=True)

# Load cost data
cost_sql = f'''
select
    year, 
    month, 
    usage_account, 
    date, 
    eks_app, 
    eks_cluster_name, 
    eks_namespace, 
    region,
    sum(ondemand_cost) AS ondemand_cost,
    sum(amortized_cost) AS amortized_cost,
    sum(net_amortized_cost) AS net_amortized_cost,
    sum(billing_cost) AS billing_cost
from {cur_database}.{cost_table}
where year='{int(args["year"])}' and month='{int(args["month"])}' 
group by 1,2,3,4,5,6,7,8
'''
print(f"Load cost with SQL: {cost_sql}\n")	
df_cost = (spark.sql(cost_sql).fillna(""))
print(f'Cost data have {len(df_cost.columns)} columns: {sorted(df_cost.columns)}\n')
df_cost.describe(['ondemand_cost','amortized_cost','net_amortized_cost','billing_cost']).show(vertical=True)

# Update column eks_flag to mark items to be allocated
df_appcost = (df_app
    .join(
        df_cost,
        ["year","month","usage_account","date", "region", "eks_app", "eks_cluster_name", "eks_namespace"], 
        "left")
)
print(f'Cost data with eks flag have {len(df_appcost.columns)} columns: {sorted(df_appcost.columns)}\n')
df_appcost.describe(['ondemand_cost','amortized_cost','net_amortized_cost','billing_cost','requests']).show(vertical=True)

print(f"Writing data to s3://{work_bucket}/data/correlate-appcost/res/")
(df_appcost.coalesce(1).write
    .mode("overwrite")
    .partitionBy(["usage_account","year","month"])
    .option("path", f"s3://{work_bucket}/data/correlate-appcost/res/")
    .saveAsTable(f"{cur_database}.enhanced_cur_correlate_appcost")
)
print(f"Job finished.")
job.commit()