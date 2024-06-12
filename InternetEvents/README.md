# Notification by wechat

This will create an lambda subscrition on AutoOps SNS topic, to send notification by wechat.

## Install

```bash
REGION=<region>
cd ~/AutoOps/InternetEvents
STACK_NAME="AutoOps$(basename $(pwd))"
BucketName=<BucketName>
sam build && sam deploy --stack-name $STACK_NAME --region $REGION --parameter-overrides BucketName=${BUCKET_NAME} --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Uninstall

```bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION --no-cli-pager
```
