# 2.ElastiCacheEvents

- This is a lamhba to format ElastiCache events and forward to eventbridge. Its execution is triggerred by Elasticache Event.

**Commands in this document are for [AWSCLIv2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). You can excecute them in [CloudShell](https://console.aws.amazon.com/cloudshell), in which these tools have been installed.**

## Deploy:

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/2.ElastiCacheEvents
EventBusName=<EventBridge Bus Name> # Eventbridge bus in the region. StepFunction or Lambda will send event to the bus.
AWS_REGION=<Guess Region>
STACK_NAME="AutoOpsElastiCacheEvents"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --parameter-overrides EventBusName=$EventBusName --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

Modify the ElastiCache replication group to sent evnet to the SNS topic created.

``` bash
SNS_TOPIC=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`SNSTopic`].OutputValue' --output text)
for i in $(aws elasticache describe-replication-groups --region $AWS_REGION --no-cli-pager --query 'ReplicationGroups[*].ReplicationGroupId' --output text)
do 
    aws elasticache modify-replication-group --region $AWS_REGION --no-cli-pager --replication-group-id ${i} --notification-topic-arn ${SNS_TOPIC} --notification-topic-status active --apply-immediately --no-cli-pager
done

```

## Start Manually

``` bash
LAMBDA_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`ForwardFunction`].OutputValue' --output text)
base64 ./examples/SnapshotComplete.json > /tmp/SnapshotComplete.base64
aws lambda invoke --region ap-northeast-1 --function-name $LAMBDA_NAME --payload /tmp/SnapshotComplete.base64 out.log
```

## Check the execution

``` bash
aws logs tail /aws/lambda/${LAMBDA_NAME} --region ${AWS_REGION} --follow
```

## Uninsatll
``` bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```

