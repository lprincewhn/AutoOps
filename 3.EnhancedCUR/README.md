# EnhancedCUR

These are AWS Glue ETL jobs to process the CUR data.


## 1. Install

```bash
AWS_REGION=<region>
cd ~/AutoOps/3.EnhancedCUR
STACK_NAME="AutoOpsEnhancedCUR"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --confirm-changeset --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides CURBucketName=${CURBucketName} WorkBucketName=${WorkBucketName} CURDatabase=${CURDatabase} CURTable=${CURTable} \
    EnhancedCURDataSetId=${EnhancedCURDataSetId} AppCostDataSetId=${AppCostDataSetId} --s3-bucket ${WorkBucketName} --s3-prefix script
aws s3 cp ./requirement.txt s3://${WorkBucketName}/
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

## 4. Jobs

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

This job loads eks resource metrics (cpu and memory reserved and actual usage) from CloudWatch ContainerInsights log group. 

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

This job loads eks resource metrics (cpu and memory reserved and actual usage) from Prometheus. Please config your prometheus as: 

1. Configure kube-state-metrics to fetch pod labels by argument "--metric-labels-allowlist"
```
    spec:
      containers:
        - name: kube-state-metrics
          image: registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.13.0
          args:
            - '--port=8080'
            - '--metric-labels-allowlist=pods=[app,app.kubernetes.io/name]' # Fetch labels "app" and "app.kubernetes.io/name" of pods.
```

2. Configure prometheus server to keep the data for at least 2 month by argument "--storage.tsdb.retention.time=65d"
```
        - name: prometheus-server
          image: quay.io/prometheus/prometheus:v2.54.1
          args:
            - '--storage.tsdb.retention.time=65d'
            - '--config.file=/etc/config/prometheus.yml'
            - '--storage.tsdb.path=/data'
            - '--web.console.libraries=/etc/prometheus/console_libraries'
            - '--web.console.templates=/etc/prometheus/consoles'
            - '--web.enable-lifecycle'
```

3. Configure ConfigMap of prometheus server to put EC2 instance ID in metric lables. Following example is to get the EC2 instance ID from annotation added by Amazon EBS or EFS CSI driver.
```
    - job_name: kubernetes-nodes-cadvisor
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - action: labelmap
        regex: __meta_kubernetes_node_annotation_csi_volume_kubernetes_io_(.+) # Fectch node annotation as metric labels
```

This job load eks resource metrics by following PromQL:

```promsql
Acutal CPU:
	sum(sum_over_time(rate(container_cpu_usage_seconds_total{image!=""}[1h])[1d:1h]))
	by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,pod,nodeid)
	*on(pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))
	by(label_app,label_app_kubernetes_io_name,pod)

Acutal Memory: 
	sum(sum_over_time(avg_over_time(container_memory_working_set_bytes{image!=""}[1h])[1d:1h]))
	by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,nodeid,pod)
	*on(pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))
	by(label_app,label_app_kubernetes_io_name,pod)

Actual NetworkIn: 
	avg(avg_over_time(kube_pod_info{host_network="false"}[1d]))by(pod)
	*on(pod)group_right()sum(sum_over_time(increase(container_network_receive_bytes_total[1h])[1d:1h]))
	by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,nodeid,pod)
	*on(pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))
	by(label_app,label_app_kubernetes_io_name,pod)
	
Actual NetworkOut: 
	avg(avg_over_time(kube_pod_info{host_network="false"}[1d]))by(pod)
	*on(pod)group_right()sum(sum_over_time(increase(container_network_transmit_bytes_total[1h])[1d:1h]))
	by(topology_kubernetes_io_region,alpha_eksctl_io_cluster_name,namespace,nodeid,pod)
	*on(pod)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_pod_labels[1d]))
	by(label_app,label_app_kubernetes_io_name,pod)
	
Reserved CPU: 
	sum(sum_over_time(avg_over_time(kube_pod_container_resource_requests{resource="cpu"}[1m])[1d:1m]))
	by(namespace,pod)/60

Reserved Memory: 
	sum(sum_over_time(avg_over_time(kube_pod_container_resource_requests{resource="memory"}[1m])[1d:1m]))
	by(namespace,pod)/60

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
There are 3 allocation algorithms. You can also customize your algorithm.

1. Only allocate EKS EC2 cost (allocate-eks-0.py)
2. Allocate EKS EC2 and DataTransfer cost (allocate-eks-1.py)
3. Allocate EKS EC2 and DataTransfer cost with non-allcated usage (allocate-eks-2.py)

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
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/allocate-eks-0.py \
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

### 4.6 LoadPrometheusAPPMetricsJob

This job loads application or business metrics, such as request of ingress (managed by ingress-nginx-controller), which can be correlated to cost, and help caculate the unit cost for business.

1. Configure kube-state-metrics to fetch ingress labels by argument "--metric-labels-allowlist"
``` bash
    spec:
      containers:
        - name: kube-state-metrics
          image: registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.13.0
          args:
            - '--port=8080'
            - '--metric-labels-allowlist=pods=[app,app.kubernetes.io/name],ingresses=[app,app.kubernetes.io/name]' # Fetch labels "app" and "app.kubernetes.io/name" of pods and ingresses.
```

2. Add labels of "cluster-name" and "region" on service "ingress-nginx-controller"
``` bash
kubectl label service ingress-nginx-controller cluster-name=<your-cluster-name> region=<your-region>
```

3. Add labels of "cluster-name" and "region" on service "kube-state-metrics"
``` bash
kubectl label service kube-state-metrics cluster-name=<your-cluster-name> region=<your-region>
```

```
Ingress Requests:
	sum(sum_over_time(increase(nginx_ingress_controller_requests[1h])[1d:1h]))
	by(ingress,region,cluster_name,namespace)
	*on(ingress)group_left(label_app,label_app_kubernetes_io_name)avg(avg_over_time(kube_ingress_labels[1d]))
	by(label_app,label_app_kubernetes_io_name,ingress)
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
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/load_prometheus_appmetrics.py \
    --work-bucket cur-597377428377 \
    --year 2024 \
    --month 12 \
    --tags-fields name
    --enable-glue-datacatalog true \
    --cur-database $CURDatabase \
    --verbose 0
```

### 4.7 CorrelateAPPCostJob

This Job correlates app metrics and cost by joining 2 tables on "eks_app", and then unit cost of the app can be caculated.

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
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/correlate_appcost.py \
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
