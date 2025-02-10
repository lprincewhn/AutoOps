# EnhancedCUR

These are AWS Glue ETL jobs to process the CUR data.


## 1. Install

```bash
AWS_REGION=<region>
cd ~/AutoOps/3.EnhancedCUR
STACK_NAME="AutoOpsEnhancedCUR"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --confirm-changeset --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides CURBucketName=${CURBucketName} WorkBucketName=${WorkBucketName} CURDatabase=${CURDatabase} CURTable=${CURTable}\
    SubnetId=${SubnetId} AvailabilityZone=${AvailabilityZone} SecurityGroupIdList=${SecurityGroupIdList} \
    --s3-bucket ${WorkBucketName} --s3-prefix script
```

## 2. Start

### Option 1: Start the state machine 

``` bash
# Start
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`EnhanceCURStateMachine`].OutputValue' --output text)
EXECUTION_ARN=$(aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --region $AWS_REGION --no-cli-pager --query 'executionArn' --input '{"time": "2025-02-03T07:58:40Z"}' --output text)
echo $EXECUTION_ARN

# Check the execution
aws stepfunctions describe-execution --execution-arn $EXECUTION_ARN --region $AWS_REGION --no-cli-pager
```

### Option 2: Invoke the lamba to start the state machine for last or specific month

``` bash
# Start
LAMBDA_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`StartupFunction`].OutputValue' --output text)
aws lambda invoke /tmp/response.json --function-name ${LAMBDA_NAME} --region $AWS_REGION --payload '{"year":"2024", "month":"12"}' --cli-binary-format raw-in-base64-out 

# Check the execution
cat /tmp/response.json
aws logs tail /aws/lambda/${LAMBDA_NAME} --region ${AWS_REGION} --follow
```

### Option 3: Start a glue job

``` bash
# Start
GLUE_JOB_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`AllocateUntagJob`].OutputValue' --output text)
JOB_RUN_ID=$(aws glue start-job-run --job-name $GLUE_JOB_NAME --region $AWS_REGION --no-cli-pager --output text --query 'JobRunId' --arguments '{"--enable-glue-datacatalog":"true", "--cur-database":"athenacurcfn_c_u_r_athena","--cur-table":"enhanced_cur","--work-bucket":"cur-597377428377","--year":"2024", "--month":"4", "--tags-fields":"resource_tags_user_project"}')
echo $JOB_RUN_ID

# Check the execution
aws glue get-job-run --job-name $GLUE_JOB_NAME --region $AWS_REGION --run-id  $JOB_RUN_ID --no-cli-pager
aws logs tail /aws-glue/jobs/output --region $AWS_REGION --follow
```

## 3. Uninstall

```bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```

## 4. Introduction of Jobs

### 4.1 StandardizeJob

This job generates tables with 20 dimensions and 8 mesurements with following SQL. You can add more dimensions with other tags, such as 'Project'.

``` sql
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
where year='{args["year"]}' and month='{int(args["month"])}' 
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21
```

**Run in local docker with following command**
``` bash
docker run -it --rm \
    -v ~/.aws:/home/glue_user/.aws \
    -v $(pwd)/:/home/glue_user/workspace/ \
    -e DISABLE_SSL=true \
    -e AWS_REGION=us-east-1 \
    -p 18080:18080 \
    -p 4040:4040 \
    --name glue_spark_submit \
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/standardize.py \
    --work-bucket cur-597377428377 \
    --year 2024 \
    --month 12 \
    --enable-glue-datacatalog true \
    --cur-database $CURDatabase \
    --cur-table $CURTable \
    --verbose 0
```

### 4.2 LoadCloudWatchEKSMetricsJob

This job load eks resource metrics (cpu and memory reserved and actual usage) from CloudWatch ContainerInsights log group. 

```CloudWatch LogInsights
filter !isempty(kubernetes.pod_name) 
| fields datefloor(Timestamp, 1h) as date, 
    concat(InstanceId,":pod/",ClusterName,"/",kubernetes.namespace_name,"/",kubernetes.pod_name) as resource_id, 
    kubernetes.labels.app as app, 
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
by date,resource_id,project,name,instance
```

**Run in local docker with following command**
``` bash
docker run -it --rm \
    -v ~/.aws:/home/glue_user/.aws \
    -v $(pwd)/:/home/glue_user/workspace/ \
    -e DISABLE_SSL=true \
    -e AWS_REGION=us-east-1 \
    -p 18080:18080 \
    -p 4040:4040 \
    --name glue_spark_submit \
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/load_cloudwatch_eksmetrics.py \
    --work-bucket cur-597377428377 \
    --year 2024 \
    --month 12 \
    --enable-glue-datacatalog true \
    --cur-database $CURDatabase \
    --usage-account $EKS_ACCOUNT \
    --region $EKS_REGION \
    --container-insights-loggroup $EKS_ContainerInsightLogGroup \
    --verbose 0
```

### 4.3 LoadPrometheusEKSMetricsJob

This job load eks resource metrics (cpu and memory reserved and actual usage) from Prometheus. Please config your prometheus as: 

1. The Prometheus scraper jobs to fetch the node annotation as labels in the node metrics. These labels will be populated into pod metrics by kubernetes scraper.
``` yaml
    - job_name: kubernetes-nodes-cadvisor
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - action: labelmap
        regex: __meta_kubernetes_node_annotation_(.+) # Fetch node annotation as metric labels
      - replacement: kubernetes.default.svc:443
        target_label: __address__
      - regex: (.+)
        replacement: /api/v1/nodes/$1/proxy/metrics/cadvisor
        source_labels:
        - __meta_kubernetes_node_name
        target_label: __metrics_path__
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
```

2. Configure kube-state-metrics to fetch the pod labels by argument "--metric-labels-allowlist=pods=[xxx,xxx]"
```
    spec:
      containers:
        - name: kube-state-metrics
          image: registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.13.0
          args:
            - '--port=8080'
            - '--metric-labels-allowlist=pods=[app]' # Fetch pod labels app.
```

This job load eks resource metrics by following PromQL:

```promsql
CPU:
sum(rate(container_cpu_usage_seconds_total{image!=""}[1h]))by(topology_kubernetes_io_region,csi_volume_kubernetes_io_nodeid,alpha_eksctl_io_cluster_name,namespace,pod)*100*on(pod)group_left(label_app)kube_pod_labels

Memory: 
sum(container_memory_working_set_bytes{image!=""})by(topology_kubernetes_io_region, csi_volume_kubernetes_io_nodeid, alpha_eksctl_io_cluster_name, namespace, pod)*on(pod)group_left(label_app)kube_pod_labels

NetworkIn: 
avg(kube_pod_info{host_network="false"})by(pod)*on(pod)group_right()sum(increase(container_network_receive_bytes_total[1h]))by(topology_kubernetes_io_region,csi_volume_kubernetes_io_nodeid,alpha_eksctl_io_cluster_name,namespace,pod)*on(pod)group_left(label_app)avg(kube_pod_labels)by(pod, label_app)

NetworkOut: 
avg(kube_pod_info{host_network="false"})by(pod)*on(pod)group_right()sum(increase(container_network_transmit_bytes_total[1h]))by(topology_kubernetes_io_region,csi_volume_kubernetes_io_nodeid,alpha_eksctl_io_cluster_name,namespace,pod)*on(pod)group_left(label_app)avg(kube_pod_labels)by(pod, label_app)
```

**Run in local docker with following command**
``` bash
docker run -it --rm \
    -v ~/.aws:/home/glue_user/.aws \
    -v $(pwd)/:/home/glue_user/workspace/ \
    -e DISABLE_SSL=true \
    -e AWS_REGION=us-east-1 \
    -p 18080:18080 \
    -p 4040:4040 \
    --name glue_spark_submit \
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/load_prometheus_eksmetrics.py \
    --work-bucket cur-597377428377 \
    --year 2024 \
    --month 12 \
    --enable-glue-datacatalog true \
    --cur-database $CURDatabase \
    --usage-account $EKS_ACCOUNT \
    --region $EKS_REGION \
    --prometheus-endpoint $EKS_Prometheus_Endpoint \
    --verbose 0
```

### 4.4 AllocateEksJob

This Job allocates the EC2 instance cost of EKS cluster to pod according its cpu and memory reserved and actual usage.

**Run in local docker with following command**
``` bash
docker run -it --rm \
    -v ~/.aws:/home/glue_user/.aws \
    -v $(pwd)/:/home/glue_user/workspace/ \
    -e DISABLE_SSL=true \
    -e AWS_REGION=us-east-1 \
    -p 18080:18080 \
    -p 4040:4040 \
    --name glue_spark_submit \
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/allocate-eks.py \
    --work-bucket cur-597377428377 \
    --year 2024 \
    --month 12 \
    --enable-glue-datacatalog true \
    --cur-database $CURDatabase \
    --standardize-table enhanced_cur_standardize \
    --eksmetrics-table enhanced_cur_eksmetrics_prometheus \
    --verbose 0
```

### 4.5 AllocateUntagJob

This Job allocates untagged cost.

**Run in local docker with following command**
``` bash
docker run -it --rm \
    -v ~/.aws:/home/glue_user/.aws \
    -v $(pwd)/:/home/glue_user/workspace/ \
    -e DISABLE_SSL=true \
    -e AWS_REGION=us-east-1 \
    -p 18080:18080 \
    -p 4040:4040 \
    --name glue_spark_submit \
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/allocate-untag.py \
    --work-bucket cur-597377428377 \
    --year 2024 \
    --month 12 \
    --tags-fields name
    --enable-glue-datacatalog true \
    --cur-database $CURDatabase \
    --verbose 0
```

## 5. Tunning jobs in loal Jupyter Notebook    

``` bash
docker run -it --rm \
    -v ~/.aws:/home/glue_user/.aws \
    -v $(pwd):/home/glue_user/workspace/jupyter_workspace/ \
    -e DISABLE_SSL=true \
    -p 4040:4040 \
    -p 18080:18080 \
    -p 8998:8998 \
    -p 8888:8888 \
    --name glue_jupyter_lab \
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 /home/glue_user/jupyter/jupyter_start.sh
```
