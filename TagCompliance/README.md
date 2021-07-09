# Tag Compliance Check

This state machine check tags of AWS resources periodly and notify users when tags are not compliant with users' requirement.

![](doc/TagCompliance.png)

## Trigger

Scheduled event from Cloudwatch. Defaultly it will do checking every day.


* Following command are for AWSCLIv2, if you are using v1, please remove the --no-cli-pager option.

## Deploy 

```
# MAIN_REGION=<main region>
# SNS_TOPIC_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsCommon --region $MAIN_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`SNSTopic`].OutputValue' --output text)
# cd ~/AutoOps/TagCompliance
# REGION=<region>
# sam build
# sam deploy --stack-name AutoOpsTagCompliance --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Start

```
# STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsTagCompliance --region us-east-1 --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`TagComplianceStateMachine`].OutputValue' --output text)
# aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --input '{}' --region $REGION --no-cli-pager
```

## Uninstall

```
# aws cloudformation delete-stack --stack-name AutoOpsTagCompliance --region $REGION --no-cli-pager
```