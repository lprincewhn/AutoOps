# EC2 Provision

- State machine to create/delete alarms for EC2 instances when they are started/terminated.

    ![](doc/EC2Provision.png)

## Prerequisite

This state machine was triggered by CloudTrail events so you need to create a trail to enable the event.

[https://console.aws.amazon.com/cloudtrail/home](https://console.aws.amazon.com/cloudtrail/home)

## Deploy 

```
# MAIN_REGION=<main region>
# SNS_TOPIC_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsCommon --region $MAIN_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`SNSTopic`].OutputValue' --output text)
# cd ~/AutoOps/EC2Provision
# REGION=<region>
# sam build
# sam deploy --stack-name AutoOpsEC2Provision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Start

```
# STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsEC2Provision --region $REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`EC2ProvisionStateMachine`].OutputValue' --output text)
# aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --input file://./examples/example_ec2_start.json --region $REGION --no-cli-pager
```
