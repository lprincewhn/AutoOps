# Process CloudWatch alarms and send notifications

State machine to process Cloudwatch alarms and send notifications to operators.

![](doc/AlarmProcessor.png)

* Following command are for AWSCLIv2, if you are using v1, please remove the --no-cli-pager option.

## Deploy 

```
# MAIN_REGION=<main region>
# SNS_TOPIC_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsCommon --region $MAIN_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`SNSTopic`].OutputValue' --output text)
# cd ~/AutoOps/AlarmProcessor
# REGION=<region>
# sam build
# sam deploy --stack-name AutoOpsAlarmProcessor --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Start

```
# STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsAlarmProcessor --region us-east-1 --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`AlarmProcessorStateMachine`].OutputValue' --output text)
# aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --input file://./examples/ES_FreeStorageSpace_alarm_example.json --region $REGION --no-cli-pager
```
