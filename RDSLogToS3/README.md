# RDSLogToS3

- A Lambda function to download rds log file and put it into S3 bucket.

**Commands in this document are for [AWSCLIv2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). You can excecute them in [CloudShell](https://console.aws.amazon.com/cloudshell), in which these tools have been installed.**

## Deploy option

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/RDSLogToS3
AWS_REGION=<region>
STACK_NAME="AutoOps$(basename $(pwd))"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

**Note: A samble EventBridge rule "demodb_audit_log_to_s3" will be deployed. Please refer it to add the rules for your RDS instances.**

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