select
	year,
	month,
	line_item_line_item_type as charge_type,
	case when bill_billing_entity='AWS' then 'AWS' else line_item_legal_entity end as billing_entity,
	case when length(product_servicename)>0 then product_servicename else product_product_name end as service, 
	product_region as region,
	product_instance_type as instance_type,
	regexp_extract(product_instance_type, '([a-z][1-9].{0,1})\.', 1) as instance_family,
	product_database_engine as database_engine,
	line_item_usage_type as usage_type,
	case when line_item_line_item_type like '%Usage' then date(line_item_usage_start_date) else date(bill_billing_period_start_date) end as usage_date,
	line_item_usage_account_id as usage_account,
	line_item_resource_id as resource_id,
	resource_tags_user_project as project,
	'na' as customer_dim2,
	'na' as customer_dim3,
	'na' as customer_dim4,
	'na' as customer_dim5,
	sum(line_item_usage_amount) as usage_amount,
	sum(cast(NULLIF(TRIM(product_vcpu), '') as decimal)*line_item_usage_amount) as vcpus,
	sum(COALESCE(cast(NULLIF(regexp_extract(product_memory, '([\.|0-9]{1,6}) GiB', 1), '') as decimal), cast(NULLIF(TRIM(product_memory_gib), '') as decimal))*line_item_usage_amount) as memory_gb,
	sum(case
	    when line_item_line_item_type='PrivateRateDiscount' then 0
	    when line_item_line_item_type='EdpDiscount' then 0
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
	    when line_item_line_item_type='PrivateRateDiscount' then 0
	    when line_item_line_item_type='EdpDiscount' then 0
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
	    when line_item_line_item_type='PrivateRateDiscount' then 0
	    when line_item_line_item_type='EdpDiscount' then 0
	    when line_item_line_item_type='SavingsPlanNegation' then 0
	    when line_item_line_item_type='SavingsPlanUpfrontFee' then 0
	    when line_item_line_item_type='Fee' and length(reservation_reservation_a_r_n)>0 then 0
	    when line_item_line_item_type='DiscountedUsage' then reservation_net_effective_cost
	    when line_item_line_item_type='Usage' then line_item_net_unblended_cost
	    when line_item_line_item_type='SavingsPlanCoveredUsage' then savings_plan_net_savings_plan_effective_cost
	    when line_item_line_item_type='RIFee' then reservation_net_unused_amortized_upfront_fee_for_billing_period+reservation_net_unused_recurring_fee
	    when line_item_line_item_type='SavingsPlanRecurringFee' then (savings_plan_amortized_upfront_commitment_for_billing_period+savings_plan_recurring_commitment_for_billing_period-savings_plan_used_commitment)*(case when is_nan(line_item_net_unblended_cost/line_item_unblended_cost) then savings_plan_net_amortized_upfront_commitment_for_billing_period/savings_plan_amortized_upfront_commitment_for_billing_period else line_item_net_unblended_cost/line_item_unblended_cost end)
	    else line_item_net_unblended_cost end) as net_amortized_cost,
	sum(line_item_unblended_cost) as billing_cost
from {{CUR_DATABASE}}.{{CUR_TABLE}}
where line_item_usage_start_date >= DATE_TRUNC('month', CURRENT_DATE) - interval '24' month
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17