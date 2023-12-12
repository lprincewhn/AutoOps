# RDSLogToS3

- A Lambda function to download rds log file and put it into S3 bucket.

**Commands in this document are for [AWSCLIv2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). You can excecute them in [CloudShell](https://console.aws.amazon.com/cloudshell), in which these tools have been installed.**

## Deploy

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/RDSLogToS3
AWS_REGION=<region>
STACK_NAME="AutoOps$(basename $(pwd))"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

**Note: A samble EventBridge rule "demodb_audit_log_to_s3" will be deployed. Please refer it to add rules for your RDS instances.**


CREATE EXTERNAL TABLE `rds_audit_log`(
  `time` string COMMENT 'from deserializer',
  `serverhost` string COMMENT 'from deserializer',
  `username` string COMMENT 'from deserializer',
  `host` string COMMENT 'from deserializer',
  `connectionid` string COMMENT 'from deserializer',
  `queryid` string COMMENT 'from deserializer',
  `operation` string COMMENT 'from deserializer',
  `database` string COMMENT 'from deserializer',
  `object` string COMMENT 'from deserializer',
  `retcode` string COMMENT 'from deserializer')
PARTITIONED BY (
  `instancename` string,
  `uploaddate` date)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ("separatorChar" = ",", "quoteChar" = "'", "escapeChar" = "\n" )
LOCATION
  's3://rds-logs.5973777428377.ap-northeast-1/'
TBLPROPERTIES (
  'projection.enabled'='true',
  "projection.instancename.type" = "injected",
  'projection.uploaddate.format'='yyyy-MM-dd',
  'projection.uploaddate.interval'='1',
  'projection.uploaddate.interval.unit'='DAYS',
  'projection.uploaddate.range'='2023-01-01,NOW',
  'projection.uploaddate.type'='date',
  'storage.location.template'='s3://rds-logs.5973777428377.ap-northeast-1/${uploaddate}/${instancename}')

## Uninsatll
``` bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```