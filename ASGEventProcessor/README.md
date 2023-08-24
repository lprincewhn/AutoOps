# Process PHD events and send notifications

State machine to process AWS Auto Scaling Group events and send notifications to administrators.



* Following command are for AWSCLIv2, if you are using v1, please remove the --no-cli-pager option.

## Deploy 

``` bash
MAIN_REGION=<main region>
SNS_TOPIC_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsCommon --region $MAIN_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`SNSTopic`].OutputValue' --output text)
cd ~/AutoOps/ASGEventProcessor
cp -p workflows/state.asl.yaml ./
REGION=<region>
sam build
sam deploy --stack-name AutoOpsASGEventProcessor --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Start

``` bash
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsASGEventProcessor --region $REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`PhdEventProcessor`].OutputValue' --output text)
aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --input file://./examples/Phd_event_example.json --region $REGION --no-cli-pager
```

## Uninstall

```
# aws cloudformation delete-stack --stack-name AutoOpsPhdEventProcessor --region $REGION --no-cli-pager
```
