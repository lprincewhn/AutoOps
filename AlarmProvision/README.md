# Alarm Provision

- State machine to create/delete alarms.

## Deploy 

```
# SNS_TOPIC_ARN=<Your SNS Topic receive notification>
# cd ~/AutoOps/RDSProvision
# AWS_REGION=<region>
# sam build
# sam deploy --stack-name AutoOpsAlarmProvision --region $AWS_REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Start

```
# STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsAlarmProvision --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`AlarmProvisionStateMachine`].OutputValue' --output text)
# EXECUTION_ARN=$(aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --region $AWS_REGION --no-cli-pager --query 'executionArn' --output text)
# aws stepfunctions describe-execution --execution-arn $EXECUTION_ARN --rgeion $AWS_REGION --no-cli-pager
```
