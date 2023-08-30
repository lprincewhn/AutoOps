# AlarmProvision

- State machine to create/delete alarms.

## Deploy option #1: w/o additional CloudWatch allarm notification

**Note: Should be used if AlarmProcessor is deployed.**

``` bash
AUTO_OPS_TOPIC=<SNS topic receive AutoOps notification> # Messages of this topic will be sent by StepFunction or Lambda, should be in the home region
cd ~/AutoOps/AlarmProvision
AWS_REGION=<region>
sam build
sam deploy --stack-name AutoOpsAlarmProvision --region $AWS_REGION --parameter-overrides AutoOpsTopicArn=$AUTO_OPS_TOPIC --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Deploy option #2: w/i additional CloudWatch allarm notification

**Note: Should be used if AlarmProcessor is not deployed.**

``` bash
AUTO_OPS_TOPIC=<SNS topic receive AutoOps notification> # Messages of this topic will be sent by StepFunction or Lambda, should be in the home region
ALARM_NOTIY_TOPIC=<Additional SNS topic receive Cloudwatch alarm notification> # Must in the same region as this SAM appliction
cd ~/AutoOps/AlarmProvision
AWS_REGION=<region>
sam build
sam deploy --stack-name AutoOpsAlarmProvision --region $AWS_REGION --parameter-overrides AutoOpsTopicArn=$AUTO_OPS_TOPIC AlarmNotifyTopicArn=$ALARM_NOTIY_TOPIC --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Start

``` bash
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsAlarmProvision --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`AlarmProvisionStateMachine`].OutputValue' --output text)
EXECUTION_ARN=$(aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --region $AWS_REGION --no-cli-pager --query 'executionArn' --output text)
echo $EXECUTION_ARN
```

## Check the result

``` bash
aws stepfunctions describe-execution --execution-arn $EXECUTION_ARN --region $AWS_REGION --no-cli-pager
```
