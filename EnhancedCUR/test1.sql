create table test1
WITH (
     format = 'TEXTFILE', 
     external_location = 's3://${WorkBucketName}/data/test') 
as
SELECT 
    date '2024-07-02' as usage_date, 
    'xxxx' as usage_account,
    'xxxx' as service,
    'xxxx' as region,
    'xxxx' as resource_id,
    'xxxx' as usage_type,
    'xxxx' as charge_type,
    'sporty' as resource_tags_user_user_costowner, 
    'uat' as resource_tags_user_user_environment, 
    100 as ondemand_cost,
    100 as amortized_cost,
    100 as billing_cost,
    '2024' as year,
    '07' as month
union
SELECT 
    date '2024-07-02' as usage_date, 
    'xxxx' as usage_account,
    'xxxx' as service,
    'xxxx' as region,
    'xxxx' as resource_id,
    'xxxx' as usage_type,
    'xxxx' as charge_type,
    'sporty' as resource_tags_user_user_costowner, 
    null as resource_tags_user_user_environment, 
    100 as ondemand_cost,
    100 as amortized_cost,
    100 as billing_cost,
    '2024' as year,
    '07' as month
union
SELECT 
    date '2024-07-02' as usage_date, 
    'xxxx' as usage_account,
    'xxxx' as service,
    'xxxx' as region,
    'xxxx' as resource_id,
    'xxxx' as usage_type,
    'xxxx' as charge_type,
    null as resource_tags_user_user_costowner, 
    'stg' as resource_tags_user_user_environment, 
    100 as ondemand_cost,
    100 as amortized_cost,
    100 as billing_cost,
    '2024' as year,
    '07' as month
union
SELECT 
    date '2024-07-02' as usage_date, 
    'xxxx' as usage_account,
    'xxxx' as service,
    'xxxx' as region,
    'xxxx' as resource_id,
    'xxxx' as usage_type,
    'xxxx' as charge_type,
    null as resource_tags_user_user_costowner, 
    null as resource_tags_user_user_environment, 
    99 as ondemand_cost,
    99 as amortized_cost,
    99 as billing_cost,
    '2024' as year,
    '07' as month
union
SELECT 
    date '2024-07-03' as usage_date, 
    'xxxx' as usage_account,
    'xxxx' as service,
    'xxxx' as region,
    'xxxx' as resource_id,
    'xxxx' as usage_type,
    'xxxx' as charge_type,
    null as resource_tags_user_user_costowner, 
    null as resource_tags_user_user_environment, 
    80 as ondemand_cost,
    80 as amortized_cost,
    80 as billing_cost,
    '2024' as year,
    '07' as month
