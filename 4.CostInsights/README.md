# CostInsightsDashboard

This is a QuickSight Dashboard to provide cost insights by drilling down on AWS CUR data.

### Install with AWSCLI

1. Prepare the environment

``` bash
export AwsAccountId=<AWS Account Id>
export AWS_REGION=us-east-1
export QuickSightUser=<QuickSignt User> # IAM User or IAM role + session name
```

2. Create Datasource

```bash

# DataSource
DataSourceId=$(cat create-data-source.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{QuickSightUser}}/${QuickSightUser}/g" \
| sed "s/{{DataSourceId}}/$(uuidgen)/g" \
| xargs -0 aws quicksight create-data-source --region ${AWS_REGION} --no-cli-pager --output text --query 'DataSourceId' --cli-input-json)

# If datasource exist already, get its id and save it to environment variable DataSourceId.
DataSourceId=$(aws quicksight list-data-sources --region ${AWS_REGION} --no-cli-pager --aws-account-id ${AwsAccountId} --output text --query 'DataSources[?Name==`Athena`].[DataSourceId]')
```

3. Create DataSet

```bash

# DataSet (CUR_SPICE)
cat data-set-spice.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{QuickSightUser}}/${QuickSightUser}/g" \
| sed "s/{{DataSourceId}}/${DataSourceId}/g" \
| sed "s/{{CURDatabase}}/${CURDatabase}/g" \
| sed "s/{{CURTable}}/${CURTable}/g" \
| sed "s/{{DataSetId}}/$(uuidgen)/g" > /tmp/create-data-set.json
CUR_SPICE_DataSetId=$(aws quicksight create-data-set --region ${AWS_REGION} --no-cli-pager --output text --query 'DataSetId' --import-mode SPICE --name "CUR SPICE" --cli-input-json file:///tmp/create-data-set.json)

# You may need to modify the SQL to adapt your CUR table properties, like database name, table name, some missing columns

cat put-data-set-refresh-properties.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{DataSetId}}/${CUR_SPICE_DataSetId}/g" \
| xargs -0 aws quicksight put-data-set-refresh-properties --region ${AWS_REGION} --no-cli-pager --cli-input-json

cat create-refresh-schedule.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{DataSetId}}/${CUR_SPICE_DataSetId}/g" \
| xargs -0 aws quicksight create-refresh-schedule --region ${AWS_REGION} --no-cli-pager --cli-input-json
  
# DataSet  (CUR_DIRECT)
# Your can also duplicate the dataset of "CUR SPICE" and update its import mode and save its id to environment variable CUR_DIRECT_DataSetId
cat data-set-direct.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{QuickSightUser}}/${QuickSightUser}/g" \
| sed "s/{{DataSourceId}}/${DataSourceId}/g" \
| sed "s/{{CURDatabase}}/${CURDatabase}/g" \
| sed "s/{{CURTable}}/${CURTable}/g" \
| sed "s/{{DataSetId}}/$(uuidgen)/g" > /tmp/create-data-set.json
CUR_DIRECT_DataSetId=$(aws quicksight create-data-set --region ${AWS_REGION} --no-cli-pager --output text --query 'DataSetId' --import-mode DIRECT_QUERY --name "CUR DIRECT" --cli-input-json file:///tmp/create-data-set.json)

# DataSet (CUR_Dimensions)
cat data-set-dimemsions.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{QuickSightUser}}/${QuickSightUser}/g" \
| sed "s/{{DataSourceId}}/${DataSourceId}/g" \
| sed "s/{{DataSetId}}/$(uuidgen)/g" > /tmp/create-data-set-dimensions.json
CUR_Dimensions_DataSetId=$(aws quicksight create-data-set --region ${AWS_REGION} --no-cli-pager --output text --query 'DataSetId' --cli-input-json file:///tmp/create-data-set-dimensions.json)
```

4. Create Analysis

```bash
# Analysis
cat analysis.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{QuickSightUser}}/${QuickSightUser}/g" \
| sed "s/{{CUR_Dimensions_DataSetId}}/${CUR_Dimensions_DataSetId}/g" \
| sed "s/{{CUR_DIRECT_DataSetId}}/${CUR_DIRECT_DataSetId}/g" \
| sed "s/{{CUR_SPICE_DataSetId}}/${CUR_SPICE_DataSetId}/g" \
| sed "s/{{AnalysisId}}/$(uuidgen)/g" > /tmp/create-analysis.json

AnalysisId=$(aws quicksight create-analysis --region ${AWS_REGION} --no-cli-pager --output text --query 'AnalysisId' --cli-input-json file:///tmp/create-analysis.json)
```

### Export as CloudFormation Template
``` bash
ExportJobId=$(aws quicksight start-asset-bundle-export-job --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --asset-bundle-export-job-id $(uuidgen) \
	--resource-arns arn:aws:quicksight:${AWS_REGION}:${AwsAccountId}:analysis/${InterSheetAnalysisId} \
	arn:aws:quicksight:${AWS_REGION}:${AwsAccountId}:analysis/${IntraSheetAnalysisId} \
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
aws quicksight delete-analysis --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --analysis-id ${InterSheetAnalysisId}
aws quicksight delete-analysis --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --analysis-id ${IntraSheetAnalysisId}
aws quicksight delete-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --no-cli-pager --data-set-id ${CUR_Dimensions_DataSetId}
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
cp data-set-dimemsions.json bk-data-set-dimemsions.json
aws quicksight describe-data-set --region ${AWS_REGION} --aws-account-id ${AwsAccountId} --data-set-id ${CUR_Dimensions_DataSetId} --no-cli-pager --query 'DataSet' > data-set-dimemsions.json
# Update above files to add AwsAccountId, DataSetId, Permissions, DataSourceArn, remove LogicalTableMap, OutputColumns, SubType
```

### Use template to share the analysis to another aws account

1. Create Template

``` bash
TemplateId=$(cat create-template.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{QuickSightUser}}/${QuickSightUser}/g" \
| sed "s/{{CUR_Dimensions_DataSetId}}/${CUR_Dimensions_DataSetId}/g" \
| sed "s/{{CUR_DIRECT_DataSetId}}/${CUR_DIRECT_DataSetId}/g" \
| sed "s/{{CUR_SPICE_DataSetId}}/${CUR_SPICE_DataSetId}/g" \
| sed "s/{{AnalysisId}}/${AnalysisId}/g" \
| sed "s/{{TemplateId}}/$(uuidgen)/g" \
| xargs -0 aws quicksight create-template --region ${AWS_REGION} --no-cli-pager --output text --query 'TemplateId' --cli-input-json)
```

2. Authorize the template to another AWS account

``` bash
cat update-template-permissions.json \
| sed "s/{{TargetAccountId}}/${TargeAwsAccountId}/g" \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{TemplateId}}/${TemplateId}/g" \
| xargs -0 aws quicksight update-template-permissions --aws-account-id ${AwsAccountId} --region ${AWS_REGION} --template-id ${TemplateId} --no-cli-pager --cli-input-json
```

3. Create dashboard in the other account from template 

``` bash
DashboardId=$(cat create-dashboard-by-template.json \
| sed "s/{{AwsAccountId}}/${AwsAccountId}/g" \
| sed "s/{{Region}}/${AWS_REGION}/g" \
| sed "s/{{QuickSightUser}}/${QuickSightUser}/g" \
| sed "s/{{CUR_Dimensions_DataSetId}}/${CUR_Dimensions_DataSetId}/g" \
| sed "s/{{CUR_DIRECT_DataSetId}}/${CUR_DIRECT_DataSetId}/g" \
| sed "s/{{CUR_SPICE_DataSetId}}/${CUR_SPICE_DataSetId}/g" \
| sed "s/{{SourceRegion}}/${SourceRegion}/g" \
| sed "s/{{SourceAwsAccountId}}/${SourceAwsAccountId}/g" \
| sed "s/{{TemplateId}}/${TemplateId}/g" \
| sed "s/{{DashboardId}}/$(uuidgen)/g" \
| xargs -0 aws quicksight create-dashboard --region ${AWS_REGION} --no-cli-pager --output text --query 'DashboardId' --name 'Cost Insights' --cli-input-json)
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


