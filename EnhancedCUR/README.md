# EnhancedCUR

These are AWS Glue ETL jobs to process the CUR data.


## Install

```bash
AWS_REGION=<region>
cd ~/AutoOps/EnhancedCUR
STACK_NAME="AutoOps$(basename $(pwd))"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --confirm-changeset --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides CURBucketName=${CURBucketName} WorkBucketName=${WorkBucketName} \
    --s3-bucket ${WorkBucketName} --s3-prefix script
```

## Start

``` bash
GLUE_JOB_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`AllocateUntagJob`].OutputValue' --output text)

JOB_RUN_ID=$(aws glue start-job-run --job-name $GLUE_JOB_NAME --region $AWS_REGION --no-cli-pager --output text --query 'JobRunId' --arguments '{"--enable-glue-datacatalog":"true", "--cur-database":"customer_cur","--cur-table":"sporty","--work-bucket":"customer-cur.597377428377","--month":"2024-04", "--tags-fields":"resource_tags_user_user_costowner"}')
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

## Cost Model
The ETL jobs will generate tables with following schema:

Column|Dimension or Measure|Field/Formula in CUR
:----|:----|:----
usage_date|Dimension|line_item_usage_start_date, date(line_item_usage_start_date)
charge_type|Dimension|line_item_line_item_type
usage_account|Dimension|line_item_usage_account_id
service|Dimension|case when length(product_servicename)>0 then product_servicename else product_product_name end
region|Dimension|product_region
usage_type|Dimension|line_item_usage_type
resource_id|Dimension|line_item_resource_id
usage_ammount|Dimension|sum(line_item_usage_amount)
resource_tags_xxx|Dimension|resource_tags_xxx
ondemand_cost|Measure|sum(case when line_item_line_item_type='SavingsPlanNegation' then 0 when line_item_line_item_type='SavingsPlanUpfrontFee' then 0 when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0 when line_item_line_item_type='DiscountedUsage' then pricing_public_on_demand_cost when line_item_line_item_type='Usage' then line_item_unblended_cost when line_item_line_item_type='SavingsPlanCoveredUsage' then pricing_public_on_demand_cost when line_item_line_item_type='RIFee' then reservation_unused_amortized_upfront_fee_for_billing_period+reservation_unused_recurring_fee when line_item_line_item_type='SavingsPlanRecurringFee' then savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment else line_item_net_unblended_cost end)
amortized_cost|Measure|sum(case when line_item_line_item_type='SavingsPlanNegation' then 0 when line_item_line_item_type='SavingsPlanUpfrontFee' then 0 when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0 when line_item_line_item_type='DiscountedUsage' then reservation_effective_cost when line_item_line_item_type='Usage' then line_item_unblended_cost when line_item_line_item_type='SavingsPlanCoveredUsage' then savings_plan_savings_plan_effective_cost when line_item_line_item_type='RIFee' then reservation_unused_amortized_upfront_fee_for_billing_period+reservation_unused_recurring_fee when line_item_line_item_type='SavingsPlanRecurringFee' then savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment else line_item_net_unblended_cost end)
billing_cost|Measure|sum(line_item_unblended_cost)