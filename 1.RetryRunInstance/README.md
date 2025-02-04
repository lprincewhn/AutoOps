# 1.RetryRunInstance

- This is a lambda to keep trying to start an EC2 instance. It will increase the chance to get scarce instance types, like GPU instance. It is triggered by a schedule rule.

**Commands in this document are for [AWSCLIv2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). You can excecute them in [CloudShell](https://console.aws.amazon.com/cloudshell), in which these tools have been installed.**

## Deploy:

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/1.RetryRunInstance
EventBusName=<EventBridge Bus Name> # Eventbridge bus in the region. StepFunction or Lambda will send event to the bus.
AWS_REGION=<Guess region>
STACK_NAME="AutoOpsRetryRunInstance"
ImageId=<Image Id>
InstanceType=<Instance Type>
KeyName=<SSH Key Name>
SecurityGroupIds=<Security Group Ids seperated by comma>
SubnetId=<Subnet Id>
InstanceCount=1
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --parameter-overrides EventBusName=$EventBusName ImageId=$ImageId InstanceType=$InstanceType KeyName=$KeyName SecurityGroupIds=$SecurityGroupIds SubnetId=$SubnetId InstanceCount=$InstanceCount --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Start Manually

``` bash
LAMBDA_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`RunInstanceFunction`].OutputValue' --output text)
aws lambda invoke /tmp/response.json --region ap-northeast-1 --function-name $LAMBDA_NAME
```

## Check the execution

``` bash
cat /tmp/response.json
aws logs tail /aws/lambda/${LAMBDA_NAME} --region ${AWS_REGION} --follow
```

## Uninsatll
``` bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```

