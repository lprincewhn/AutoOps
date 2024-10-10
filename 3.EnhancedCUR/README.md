# EnhancedCUR

These are AWS Glue ETL jobs to process the CUR data.


## Install

```bash
AWS_REGION=<region>
cd ~/AutoOps/3.EnhancedCUR
STACK_NAME="AutoOpsEnhancedCUR"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --confirm-changeset --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides CURBucketName=${CURBucketName} WorkBucketName=${WorkBucketName} CURDatabase=${CURDatabase} CURTable=${CURTable}\
    --s3-bucket ${WorkBucketName} --s3-prefix script
```

## Start

``` bash
GLUE_JOB_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`AllocateUntagJob`].OutputValue' --output text)

JOB_RUN_ID=$(aws glue start-job-run --job-name $GLUE_JOB_NAME --region $AWS_REGION --no-cli-pager --output text --query 'JobRunId' --arguments '{"--enable-glue-datacatalog":"true", "--cur-database":"athenacurcfn_c_u_r_athena","--cur-table":"enhanced_cur","--work-bucket":"cur-597377428377","--year":"2024", "--month":"4", "--tags-fields":"resource_tags_user_project"}')
echo $JOB_RUN_ID
```

## Check the execution

``` bash
aws glue get-job-run --job-name $GLUE_JOB_NAME --region $AWS_REGION --run-id  $JOB_RUN_ID --no-cli-pager
aws logs tail /aws-glue/jobs/output --region $AWS_REGION --follow
```


## Uninstall

```bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```

## StandardizeJob

This job generates tables with following schema:

Column|Dimension or Measure|Field/Formula in AWS CUR
:----|:----|:----
usage_date|Dimension|line_item_usage_start_date, date(line_item_usage_start_date)
charge_type|Dimension|line_item_line_item_type
usage_account|Dimension|line_item_usage_account_id
service|Dimension|case when length(product_servicename)>0 then product_servicename else product_product_name end
region|Dimension|product_region
instance_type|Dimension|product_instance_type
instance_family|Dimension|product_instance_type, regexp_extract(product_instance_type, '([a-z][1-9].{0,2})\.', 1)
database_engine|Dimension|database_engine
usage_type|Dimension|line_item_usage_type
resource_id|Dimension|line_item_resource_id
<<tags>>|Dimension|resource_tags_xxx

usage_ammount|Measure|sum(line_item_usage_amount)
vcpus|Measure|product_vcpu, sum(cast(case when line_item_usage_type not like '%EBSOptimized%' then TRIM(product_vcpu) else '' end as float)*line_item_usage_amount)
memory_gb|Measure|sum(cast(case when line_item_usage_type not like '%EBSOptimized%' and length(regexp_extract(product_memory, '([\.|0-9]{{1,6}}) GiB', 1))>0 then TRIM(regexp_extract(product_memory, '([\.|0-9]{{1,6}}) GiB', 1)) else TRIM(product_memory_gib) end as float)*line_item_usage_amount)
ondemand_cost|Measure|sum(case when line_item_line_item_type='SavingsPlanNegation' then 0 when line_item_line_item_type='SavingsPlanUpfrontFee' then 0 when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0 when line_item_line_item_type='DiscountedUsage' then pricing_public_on_demand_cost when line_item_line_item_type='Usage' then line_item_unblended_cost when line_item_line_item_type='SavingsPlanCoveredUsage' then pricing_public_on_demand_cost when line_item_line_item_type='RIFee' then reservation_unused_amortized_upfront_fee_for_billing_period+reservation_unused_recurring_fee when line_item_line_item_type='SavingsPlanRecurringFee' then savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment else line_item_net_unblended_cost end)
amortized_cost|Measure|sum(case when line_item_line_item_type='SavingsPlanNegation' then 0 when line_item_line_item_type='SavingsPlanUpfrontFee' then 0 when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0 when line_item_line_item_type='DiscountedUsage' then reservation_effective_cost when line_item_line_item_type='Usage' then line_item_unblended_cost when line_item_line_item_type='SavingsPlanCoveredUsage' then savings_plan_savings_plan_effective_cost when line_item_line_item_type='RIFee' then reservation_unused_amortized_upfront_fee_for_billing_period+reservation_unused_recurring_fee when line_item_line_item_type='SavingsPlanRecurringFee' then savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment else line_item_net_unblended_cost end)
net_amortized_cost|Measure|sum(case when line_item_line_item_type='PrivateRateDiscount' then 0 when line_item_line_item_type='EdpDiscount' then 0 when line_item_line_item_type='SavingsPlanNegation' then 0 when line_item_line_item_type='SavingsPlanUpfrontFee' then 0 when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0 when line_item_line_item_type='DiscountedUsage' then reservation_net_effective_cost when line_item_line_item_type='Usage' then line_item_net_unblended_cost when line_item_line_item_type='SavingsPlanCoveredUsage' then savings_plan_net_savings_plan_effective_cost when line_item_line_item_type='RIFee' then reservation_net_unused_amortized_upfront_fee_for_billing_period+reservation_net_unused_recurring_fee when line_item_line_item_type='SavingsPlanRecurringFee' then (savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment)*(case when isnan(line_item_net_unblended_cost/line_item_unblended_cost) then savings_plan_net_amortized_upfront_commitment_for_billing_period/savings_plan_amortized_upfront_commitment_for_billing_period else line_item_net_unblended_cost/line_item_unblended_cost end) else line_item_net_unblended_cost end)
billing_cost|Measure|sum(line_item_unblended_cost)

## LoadEKSMetricsJob

This job load eks resource metrics (cpu and memory reserved and actual usage) from CloudWatch ContainerInsights log group. 

```CloudWatch LogInsights
filter !isempty(kubernetes.pod_name) 
| fields datefloor(Timestamp, 1h) as usage_date, 
    concat(InstanceId,":pod/",ClusterName,"/",kubernetes.namespace_name,"/",kubernetes.pod_name) as resource_id, 
    kubernetes.labels.app as name, 
    kubernetes.labels.project as project, 
    InstanceId as instance 
| stats min(Timestamp) as start_time, 
    max(Timestamp) as end_time, 
    count(pod_cpu_usage_total) as actual_cpu_cnt, 
    sum(pod_cpu_usage_total) as actual_cpu, 
    count(pod_cpu_request) as reserved_cpu_cnt, 
    sum(pod_cpu_request) as reserved_cpu, 
    count(pod_memory_working_set) as actual_mem_cnt, 
    sum(pod_memory_working_set) as actual_mem,
    count(pod_memory_request) as reserved_mem_cnt, 
    sum(pod_memory_request) as reserved_mem 
by usage_date,resource_id,project,name,instance
```

## AllocateEksJob

This Job allocates the EC2 instance cost of EKS cluster to pod according its cpu and memory reserved and actual usage.

## AllocateUntagJob

This Job allocates untagged cost.

