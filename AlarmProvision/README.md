# AlarmProvision

- State machine to create/delete alarms.

**Commands in this document are for [AWSCLIv2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). You can excecute them in [CloudShell](https://console.aws.amazon.com/cloudshell), in which these tools have been installed.**

## Deploy option #1: without CloudWatch alarm notification of raw format in the same region

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/AlarmProvision
AutoOpsTopicArn=<SNS topic receive AutoOps notification> # Messages of this topic will be sent by StepFunction or Lambda, should be in the home region
AWS_REGION=ap-northeast-1
TargetRegions=<regions to deploy, seperated by comma> # If this variable is set, AWS_REGION will be ignored
STACK_NAME="AutoOps$(basename $(pwd))"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --parameter-overrides AutoOpsTopicArn=$AutoOpsTopicArn TargetRegions=$TargetRegions --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Deploy option #2: with CloudWatch alarm notification of raw format in the same region


``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd AutoOps/AlarmProvision
AutoOpsTopicArn=<SNS topic receive AutoOps notification> # Messages of this topic will be sent by StepFunction or Lambda, should be in the home region
AWS_REGION=ap-northeast-1
TargetRegions=<regions to deploy, seperated by comma> # If this variable is set, AWS_REGION will be ignored
RAW_ALARM_TOPIC=<Additional SNS topic receive Cloudwatch alarm notification> # Must in the same region as this SAM appliction
STACK_NAME="AutoOps$(basename $(pwd))"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --parameter-overrides AutoOpsTopicArn=$AUTO_OPS_TOPIC TargetRegions=$TARGET_REGIONS RawAlarmTopicArn=$RAW_ALARM_TOPIC --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Define Alarms
``` bash
export AlarmDefinitionBucket=<AlarmDefinitionBucket output of the stack>
aws s3 sync ./AlarmDefinitions/ s3://${AlarmDefinitionBucket}/
```

## Start

``` bash
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`AlarmProvisionStateMachine`].OutputValue' --output text)
EXECUTION_ARN=$(aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --region $AWS_REGION --no-cli-pager --query 'executionArn' --output text)
echo $EXECUTION_ARN
```

## Check the execution

``` bash
aws stepfunctions describe-execution --execution-arn $EXECUTION_ARN --region $AWS_REGION --no-cli-pager
```

## Uninsatll
``` bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```

## Default and Dedicate Threshold
Add tag "AlarmThreshold" to set dedicate threshold for each resource, the tag value should be a JSON string, like:
```
{"CPUUtilization":90, "CreditSupportMinute", 20}
```
If not set, default threshold will be used.

### ALB Targetgroup
Parameter|Default Value|Details
:----|----:|:----
UnHealthyHostCount|1|It is the threshold of UnHealthyHostCount.
TargetResponseTime|0.1|It is the threshold of TargetResponseTime.

### ALB 
Parameter|Default Value|Details
:----|----:|:----
Target5XXRate|1|It is the threshold of HTTPCode_Target_5XX_Count/RequestCount*100.

### NLB Targetgroup
Parameter|Default Value|Details
:----|----:|:----
UnHealthyHostCount|1|It is the threshold of UnHealthyHostCount.

### NLB 
Parameter|Default Value|Details
:----|----:|:----
TargetResetRate|1|It is the threshold of TCP_Target_Reset_Count/NewFlowCount*100.

### EC2 Instance
Parameter|Default Value|Details
:----|----:|:----
CPUUtilization|80|It is the threshold of CPUUtilization.
CreditSupportMinute|30|The left minutes the instances can run with 100% CPUUtilization. Adjustment is needed after the instance type changed because it depends on the number of vcpu. It will determine the threshold of CPUCreditBalance.
BaseIOPS|1|Only for instance with burst IO performacne. It will determine the threshold of EBSReadOps+EBSWriteOps. Adjustment is needed after the instance type changed.
MaxIOPS|0.8|Only for instance with consistant IO performacne. It will determine the threshold of EBSReadOps+EBSWriteOps. Adjustment is needed after the instance type changed.
BaseThroughput|1|Only for instance with burst IO performacne. It will determine the threshold of EBSReadBytes+EBSWriteBytes. Adjustment is needed after the instance type changed.
MaxThroughput|0.8|Only for instance with consistant IO performacne. It will determine the threshold of EBSReadBytes+EBSWriteBytes. Adjustment is needed after the instance type changed.
BaseNetworkBandwidth|1|Only for instance with burst IO performacne. It will determine the threshold of max(NetworkIn,NetworkOut). Adjustment is needed after the instance type changed.
MaxNetworkBandwidth|0.8|Only for instance with consistant IO performacne. It will determine the threshold of max(NetworkIn,NetworkOut). Adjustment is needed after the instance type changed.

### EBS Volume
Parameter|Default Value|Details
:----|----:|:----
IOPS|0.8|It will determine the threshold of (VolumeReadOps+VolumeWriteOps)/PERIOD. Adjustment is needed after the volume type or performance changed.
Throughput|0.8|It will determine the threshold of (VolumeReadBytes+VolumeWriteBytes)/PERIOD. Adjustment is needed after the volume type or performance changed.

### RDS DB Instance
Parameter|Default Value|Details
:----|----:|:----
CPUUtilization|80|It is the threshold of CPUUtilization.
CreditSupportMinute|30|The left minutes the instances can run with 100% CPUUtilization. Adjustment is needed after the instance type changed because it depends on the number of vcpu. It will determine the threshold of CPUCreditBalance.
FreeStorageSpaceGB|50|It will determine the threshold of FreeStorageSpace.
SwapUsageMB|50|It will determine the threshold of SwapUsage.
BaseIOPS|0.8|Only for instance with burst IO performacne. It will determine the threshold of (ReadIOPS+WriteIOPS). Adjustment is needed after the instance/volume type or its provisioned IOPS changed.
MaxIOPS|1|Only for instance with consistant IO performacne. It will determine the threshold of (ReadIOPS+WriteIOPS). Adjustment is needed after the instance/volume type or provisioned IOPS changed.
BaseThroughput|0.8|Only for instance with burst IO performacne. It will determine the threshold of ReadThroughput+WriteThroughput. Adjustment is needed after the instance/volume type or its provisioned Throughput changed.
MaxThroughput|1|Only for instance with consistant IO performacne. It will determine the threshold of ReadThroughput+WriteThroughput. Adjustment is needed after the instance/volume type or its provisioned Throughput changed.
BaseNetworkBandwidth|1|Only for instance with burst IO performacne. It will determine the threshold of max(NetworkReceiveThroughput,NetworkTransmitThroughput). Adjustment is needed after the instance type changed.
MaxNetworkBandwidth|0.8|Only for instance with consistant IO performacne. It will determine the threshold of max(NetworkReceiveThroughput,NetworkTransmitThroughput). Adjustment is needed after the instance type changed.
DatabaseConnections|0.9*(InstanceMemoryInMB-500)*1024*1024/12582880|It will determine the threshold of DatabaseConnections.

### ElastiCache for Redis Instance
Parameter|Default Value|Details
:----|----:|:----
CPUUtilization|80|It is the threshold of CPUUtilization.
EngineCPUUtilization|80|It is the threshold of EngineCPUUtilization.
CreditSupportMinute|30|The left minutes the instances can run with 100% CPUUtilization. Adjustment is needed after the instance type changed because it depends on the number of vcpu. It will determine the threshold of CPUCreditBalance.
DatabaseMemoryUsagePercentage|80|It is the threshold of DatabaseMemoryUsagePercentage.
SwapUsageMB|50|It will determine the threshold of SwapUsage.
BaseNetworkBandwidth|1|Only for instance with burst IO performacne. It will determine the threshold of max(NetworkReceiveThroughput,NetworkTransmitThroughput). Adjustment is needed after the instance type changed.
MaxNetworkBandwidth|0.8|Only for instance with consistant IO performacne. It will determine the threshold of max(NetworkReceiveThroughput,NetworkTransmitThroughput). Adjustment is needed after the instance type changed.
CurrConnections|60000|It will determine the threshold of CurrConnections.

### ElasticSearch/OpenSearch Domain
Parameter|Default Value|Details
:----|----:|:----
CPUUtilization|80|It is the threshold of CPUUtilization.
CreditSupportMinute|30|The left minutes the instances can run with 100% CPUUtilization. Adjustment is needed after the instance type changed because it depends on the number of vcpu. It will determine the threshold of CPUCreditBalance.
FreeStorageSpaceGB|20|It will determine the threshold of FreeStorageSpace.
JVMMemoryPressure|20|It is the threshold of JVMMemoryPressure.
BaseIOPS|0.8|Only for instance with burst IO performacne. It will determine the threshold of (ReadIOPSMicroBursting+WriteIOPSMicroBursting). Adjustment is needed after the instance/volume type or its provisioned IOPS changed.
MaxIOPS|1|Only for instance with consistant IO performacne. It will determine the threshold of (ReadIOPSMicroBursting+WriteIOPSMicroBursting). Adjustment is needed after the instance/volume type or provisioned IOPS changed.
BaseThroughput|0.8|Only for instance with burst IO performacne. It will determine the threshold of ReadThroughputMicroBursting+WriteThroughputMicroBursting. Adjustment is needed after the instance/volume type or its provisioned Throughput changed.
MaxThroughput|1|Only for instance with consistant IO performacne. It will determine the threshold of ReadThroughputMicroBursting+WriteThroughputMicroBursting. Adjustment is needed after the instance/volume type or its provisioned Throughput changed.
ActiveShards|30000|It is the threshold of ActiveShards.
ThreadpoolWriteQueue|100|It is the threshold of ThreadpoolWriteQueue.
AvgThreadpoolSearchQueue|500|It is the threshold of average value of ThreadpoolSearchQueue on all nodes.
MaxThreadpoolSearchQueue|5000|It is the threshold of maximum value of ThreadpoolSearchQueue on all nodes.
5XXRate|10|It is the threshold of 5xx/(OpenSearchRequests+ElasticsearchRequests)*100.

### S3 Bucket
Parameter|Default Value|Details
:----|----:|:----
5XXRate|1|It is the threshold of 5xxErrors/(AllRequests)*100.