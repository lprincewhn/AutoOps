# AlarmProvision

- State machine to create/delete alarms.

**Commands in this document are for [AWSCLIv2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). You can excecute them in [CloudShell](https://console.aws.amazon.com/cloudshell), in which these tools have been installed.**

## Deploy option #1: w/o CloudWatch alarm notification of raw format

**Note: Should be used if [AlarmProcessor](https://github.com/lprincewhn/AutoOps/tree/master/AlarmProcessor) is deployed**

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd AutoOps/CertExpirationNotify
AUTO_OPS_TOPIC=<SNS topic receive AutoOps notification> # Messages of this topic will be sent by StepFunction or Lambda, should be in the home region
cd ~/AutoOps/AlarmProvision
AWS_REGION=<region>
STACK_NAME=AutoOpsAlarmProvision
sam build
sam deploy --stack-name $STACK_NAME --region $AWS_REGION --parameter-overrides AutoOpsTopicArn=$AUTO_OPS_TOPIC --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Deploy option #2: w/i CloudWatch alarm notification of raw format

**Note: Should be used if AlarmProcessor is not deployed**

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd AutoOps/CertExpirationNotify
AUTO_OPS_TOPIC=<SNS topic receive AutoOps notification> # Messages of this topic will be sent by StepFunction or Lambda, should be in the home region
RAW_ALARM_TOPIC=<Additional SNS topic receive Cloudwatch alarm notification> # Must in the same region as this SAM appliction
AWS_REGION=<region>
STACK_NAME=AutoOpsAlarmProvision
sam build
sam deploy --stack-name $STACK_NAME --region $AWS_REGION --parameter-overrides AutoOpsTopicArn=$AUTO_OPS_TOPIC RawAlarmTopicArn=$RAW_ALARM_TOPIC --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
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
