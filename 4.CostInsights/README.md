# CostInsightsDashboard

This is a QuickSight Dashboard to provide cost insights by drilling down on AWS CUR data.

### Install with AWSCLI

1. Prepare the environment

``` bash
export AwsAccountId=<AWS Account Id>
export AWS_REGION=us-east-1
export QuickSightUser=<QuickSignt User> # IAM User or IAM role + session name
export CURDatabase=<CUR database name in Athena>
export CURTable=<CUR table name in Athena>
```

2. Create Datasource

```bash

# DataSource
export DataSourceId=$(uuidgen)
envsubst < ./create-data-source.json \
| xargs -0 aws quicksight create-data-source --region ${AWS_REGION} --no-cli-pager --cli-input-json
aws quicksight  describe-data-source --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --data-source-id ${DataSourceId} --no-cli-pager

# If datasource exist already, get its id and save it to environment variable DataSourceId.
export DataSourceId=$(aws quicksight list-data-sources --region ${AWS_REGION} --no-cli-pager --aws-account-id ${AwsAccountId} --output text --query 'DataSources[?Name==`Athena`].[DataSourceId]')
```

3. Create DataSet

```bash

# DataSet (CUR_SPICE)
export CUR_SPICE_DataSetId=$(uuidgen)
envsubst < ./data-set-spice.json  > /tmp/create-data-set-spice.json
aws quicksight create-data-set --region ${AWS_REGION} --no-cli-pager --import-mode SPICE --name "CUR SPICE" --cli-input-json file:///tmp/create-data-set-spice.json
aws quicksight describe-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --data-set-id ${CUR_SPICE_DataSetId} --no-cli-pager

# You may need to modify the SQL to adapt your CUR table properties, like database name, table name, some missing columns

envsubst < ./put-data-set-refresh-properties.json \
| xargs -0 aws quicksight put-data-set-refresh-properties --region ${AWS_REGION} --no-cli-pager --cli-input-json

envsubst < ./create-refresh-schedule.json \
| xargs -0 aws quicksight create-refresh-schedule --region ${AWS_REGION} --no-cli-pager --cli-input-json
  
# DataSet  (CUR_DIRECT)
export CUR_DIRECT_DataSetId=$(uuidgen)
envsubst < ./data-set-direct.json  > /tmp/create-data-set-direct.json
aws quicksight create-data-set --region ${AWS_REGION} --no-cli-pager --import-mode DIRECT_QUERY --name "CUR DIRECT" --cli-input-json file:///tmp/create-data-set-direct.json
aws quicksight describe-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --data-set-id ${CUR_DIRECT_DataSetId} --no-cli-pager

# DataSet (CUR_Fields)
export CUR_Fields_DataSetId=$(uuidgen)
envsubst < ./data-set-fields.json  > /tmp/create-data-set-fields.json
aws quicksight create-data-set --region ${AWS_REGION} --no-cli-pager --cli-input-json file:///tmp/create-data-set-fields.json
aws quicksight describe-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --data-set-id ${CUR_Fields_DataSetId} --no-cli-pager
```

4. Create Analysis

```bash
# Analysis
export AnalysisId=$(uuidgen)
envsubst '${AwsAccountId} ${AWS_REGION} ${QuickSightUser} ${CUR_Fields_DataSetId} ${CUR_DIRECT_DataSetId} ${CUR_SPICE_DataSetId} ${AnalysisId}' < ./create-analysis.json  > /tmp/create-analysis.json
aws quicksight create-analysis --region ${AWS_REGION} --no-cli-pager --cli-input-json file:///tmp/create-analysis.json
aws quicksight describe-analysis --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --analysis-id ${AnalysisId} --no-cli-pager
```

### Export as CloudFormation Template
``` bash
ExportJobId=$(aws quicksight start-asset-bundle-export-job --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --asset-bundle-export-job-id $(uuidgen) \
	--resource-arns arn:aws:quicksight:${AWS_REGION}:${AwsAccountId}:analysis/${AnalysisId} \
	--include-all-dependencies --include-permissions --export-format CLOUDFORMATION_JSON --query 'AssetBundleExportJobId' \
	--cloud-formation-override-property-configuration '{"ResourceIdOverrideConfiguration": {"PrefixForAllResources":true}}')
DownloadUrl=$(aws quicksight describe-asset-bundle-export-job  --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --output text --asset-bundle-export-job-id ${ExportJobId} --query 'DownloadUrl')
wget ${DownloadUrl} -O cfn.json
```

### Install with CloudFormation
``` bash
STACK_NAME="AutoOpsCostInsights"
sam build --template-file ./cfn.json && sam deploy --template-file ./cfn.json --stack-name $STACK_NAME --region $AWS_REGION \
	--confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

### Uninstall with AWSCLI
``` bash
aws quicksight delete-analysis --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --analysis-id ${AnalysisId}
aws quicksight delete-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --data-set-id ${CUR_Fields_DataSetId}
aws quicksight delete-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --data-set-id ${CUR_DIRECT_DataSetId}
aws quicksight delete-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --data-set-id ${CUR_SPICE_DataSetId}
aws quicksight delete-data-source --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --data-source-id ${DataSourceId}
```

### Uninstall with CloudFormation
``` bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```

### Customization

You can update the datasets and analyses in QuickSight console. If you want persist your update to this repo, please run following to export the definition.

``` bash
cp analysis.json bk-analysis.json
aws quicksight describe-analysis-definition --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --analysis-id ${AnalysisId} --no-cli-pager > analysis.json
# Update above files to add AwsAccountId, AnalysisId, DataSourceId, Permissions
cp data-set-spice.json bk-data-set-spice.json
aws quicksight describe-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --data-set-id ${CUR_SPICE_DataSetId} --no-cli-pager --query 'DataSet' > data-set-spice.json
cp data-set-direct.json bk-data-set-direct.json
aws quicksight describe-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --data-set-id ${CUR_DIRECT_DataSetId} --no-cli-pager --query 'DataSet' > data-set-direct.json
cp data-set-fields.json bk-data-set-fields.json
aws quicksight describe-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --data-set-id ${CUR_Fields_DataSetId} --no-cli-pager --query 'DataSet' > data-set-fields.json
# Update above files to add AwsAccountId, DataSetId, Permissions, DataSourceArn, remove LogicalTableMap, OutputColumns, SubType
```

### Use template to share the analysis to another aws account

1. Create Template

``` bash
export TemplateId=$(uuidgen)
envsubst < ./create-template.json  > /tmp/create-template.json
aws quicksight create-template --region ${AWS_REGION} --no-cli-pager --cli-input-json file:///tmp/create-template.json
aws quicksight describe-template --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --template-id ${TemplateId} --no-cli-pager
```

2. Authorize the template to another AWS account

``` bash
envsubst < ./update-template-permissions.json  > /tmp/update-template-permissions.json
aws quicksight update-template-permissions --aws-account-id ${AwsAccountId} --region ${AWS_REGION} --template-id ${TemplateId} --no-cli-pager --cli-input-json file:///tmp/update-template-permissions.json
```

3. Create dashboard in the other account from template 

``` bash
export DashboardId=$(uuidgen)
envsubst < ./create-dashboard-by-template.json  > /tmp/create-dashboard-by-template.json
aws quicksight create-dashboard --region ${AWS_REGION} --no-cli-pager --output text --query 'DashboardId' --name 'Cost Insights' --cli-input-json file:///tmp/create-dashboard-by-template
aws quicksight describe-dashboard --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --dashboard-id ${DashboardId} --no-cli-pager
```

### Analysis Caculated Field

```bash
# usage_category
ifelse(
	locate({charge_type}, "SavingsPlanCovered")>0, "SP/RI",
	locate({charge_type}, "Discounted")>0, "SP/RI",
	locate({charge_type}, "RIFee")>0, "未用RI",
	locate({charge_type}, "SavingsPlanRecurring")>0, "未用SP",
	locate({usage_type}, "DataTransfer-Regional")>0, "AWS区域内部流量",
	locate({usage_type}, "AWS-Out")>0, "AWS区域之间流量",
	locate({usage_type}, "AWS-In")>0, "AWS区域之间流量",
	locate({usage_type}, "DataXfer-In")>0, "专线->AWS流量",
	locate({usage_type}, "DataXfer-Out")>0, "AWS->专线流量",
	locate({usage_type}, "DataTransfer-Out-Bytes")>0, "AWS->互联网流量",
	locate({usage_type}, "DataTransfer-In")>0, "互联网->AWS流量",
	{service}='Amazon CloudFront',
	ifelse(
		locate({usage_type},"Requests-Tier")>0,"客户端请求",
		locate({usage_type},"Requests-HTTP")>0,"回源请求",
		locate({usage_type},"DataTransfer-Out-Bytes")>0,"客户端流量",
		locate({usage_type},"DataTransfer-Out-OBytes")>0,'回源流量',
		locate({usage_type},"CloudFrontFunctions")>0,"边缘函数",
		locate({usage_type},"Lambda-Edge-Request")>0,"L@E请求次数",
		locate({usage_type},"Lambda-Edge-GB-Second")>0,"L@E资源",
		locate({usage_type},"SSL-Cert-Custom")>0,"证书",
		locate({usage_type},"OriginShield")>0,"源护盾",
		locate({usage_type},"Invalidations")>0,"缓存失效API",
		"其他CloudFront费用"
	),
	{service}='Elastic Load Balancing',
	ifelse(
		locate({usage_type},"LCUUsage")>0,"ELB处理能力",
		locate({usage_type},"LoadBalancerUsage")>0,"ELB资源",
	"其他ELB费用"
	),
	{service}='Amazon Elastic Compute Cloud',
	ifelse(
		locate({usage_type}, "BoxUsage")>0, "按需实例",
		locate({usage_type}, "SpotUsage")>0, "Spot",
		locate({usage_type}, "Snapshot")>0, "EBS快照",
		locate({usage_type}, "EBS")>0 and locate({usage_type}, "IO")>0, "EBS卷IO",
		locate({usage_type}, "EBS")>0 and locate({usage_type}, "Throughput")>0, "EBS卷吞吐量",
		locate({usage_type}, "EBSOptimized")>0, "EBS卷专用带宽",
		locate({usage_type}, "EBS")>0, "EBS卷存储",
		locate({usage_type}, "NatGateway")>0, "NAT网关",
		"其他EC2费用"
	),
	{service}='Amazon ElastiCache',
	ifelse(
		locate({usage_type},"NodeUsage")>0,"按需实例",
		locate({usage_type},"Backup")>0,"备份",
		"其他ElastiCache费用"
	),
	{service}='Amazon Relational Database Service',
	ifelse(
		locate({usage_type},"StorageIO")>0,"数据库存储IO",
		locate({usage_type},"Throughput")>0,"数据库存储吞吐量",
		locate({usage_type},"IOPS")>0,"数据库存储IO",
		locate({usage_type},"Storage")>0,"数据库存储空间",
		locate({usage_type},"InstanceUsage")>0,"按需实例",
		locate({usage_type},"Multi-AZUsage")>0,"按需实例",
		locate({usage_type},"Mirror")>0,"按需实例",
		locate({usage_type},"ProxyUsage")>0,"数据库代理",
		locate({usage_type},"Backup")>0,"备份",
		locate({usage_type},"ServerlessUsage")>0,"Serverless数据库",
		"其他RDS费用"
	),
	{service}='Amazon DynamoDB',
	ifelse(
		locate({usage_type},"TimedStorage")>0,"存储空间",
		locate({usage_type},"RequestUnit")>0,"按需请求",
		locate({usage_type},"CapacityUnit")>0,"预置容量",
		locate({usage_type},"HeavyUsage")>0,"预留容量",
		locate({usage_type},"TimedStorage")>0,"存储空间",
		locate({usage_type},"Backup")>0,"备份",
		locate({usage_type},"Restore")>0,"恢复",
		"其他DynamoDB费用"
	),
	{service}='Amazon Managed Streaming for Apache Kafka',
	ifelse(
		locate({usage_type},"Kafka.Storage")>0,"MSK存储",
		locate({usage_type},"Kafka")>0,"按需实例",
		"其他MSK费用"
	),
	{service}='Amazon OpenSearch Service',
	ifelse(
		locate({usage_type},"Storage")>0,"存储空间",
		locate({usage_type},"PIOPS")>0,"存储IO",
		locate({usage_type},"ESInstance")>0,"按需实例",
		"其他ES/AOS费用"
	),
	{service}='Amazon Redshift',
	ifelse(
		locate({usage_type},"Node")>0,"按需实例",
		locate({usage_type},"RMS")>0,"存储空间",
		locate({usage_type},"DataScan")>0,"Spectrum数据扫描",
		locate({usage_type},"CS")>0,"并发扩容",
		locate({usage_type},"Snapshot")>0,"备份",
		"其他Redshift费用"
	),
	{service}='Amazon Simple Storage Service',
	ifelse(
		locate({usage_type},"TimedStorage")>0,"存储空间",
		locate({usage_type},"Requests-")>0,"请求次数",
		locate({usage_type},"Retrieval-")>0,"数据取回",
		"其他S3费用"
	),
	{service}='Amazon Virtual Private Cloud',
	ifelse(
		locate({usage_type}, "TransitGateway")>0, "TGW",
		locate({usage_type}, "VPN")>0, "VPN",
		locate({usage_type}, "PublicIPv4")>0, "IPv4公网地址",
		locate({usage_type}, "VpcEndpoint")>0, "VPC Endpoint",
		"其他VPC费用"
	),
	{service}='AWS Direct Connect',
	ifelse(
		locate({usage_type},"PortUsage")>0,"专线端口",
		"其他DirectConnect费用"
	),
	{service}='AmazonDMS',
	ifelse(
		locate({usage_type},"Multi-AZUsg")>0,"复制实例",
		locate({usage_type},"InstanceUsg")>0,"复制实例",
		locate({usage_type},"Storage")>0,"存储",
		"其他DMS费用"
	),
	{service}='AmazonCloudWatch',
	ifelse(
		locate({usage_type},"MetricMonitorUsage")>0,"指标存储",
		locate({usage_type},"-Metrics")>0,"指标API请求",
		locate({usage_type},"Requests")>0,"指标API请求",
		locate({usage_type},"AlarmMonitorUsage")>0,"告警规则",
		locate({usage_type},"DashboardsUsageHour")>0,"监控面板",
		locate({usage_type},"TimedStorage-ByteHrs")>0,"日志存储",
		locate({usage_type},"DataProcessing-Bytes")>0,"日志处理",
		locate({usage_type},"VendedLog")>0,"AWS服务日志处理",
		locate({usage_type},"DataScan")>0,"日志查询扫描",
		locate({usage_type},"S3-Egress")>0,"日志导出到S3",
		"其他CloudWatch费用"
	),
	{service}='Amazon GuardDuty',
	ifelse(
		locate({usage_type},"EKS")>0,"EKS运行时系统监控",
		locate({usage_type},"KubernetesAuditLogs")>0,"EKS审计日志分析",
		locate({usage_type},"Lambda")>0,"Lambda网络日志分析",
		locate({usage_type},"PaidEventsAnalyzed-Bytes")>0,"VPC流日志和DNS日志分析",
		locate({usage_type},"PaidEventsAnalyzed")>0,"CloudTrail管理事件分析",
		locate({usage_type},"PaidS3DataEventsAnalyzed")>0,"S3数据事件分析",
		"其他Guardduty费用"
	),
	"其他"
)

# charge_category
ifelse(
    locate({service}, 'Support')>0, '技术支持',
    right({charge_type}, 5)='Usage', '产品',
    '其他'
)
```


