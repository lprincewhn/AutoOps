# Notification by wechat

This will create an lambda subscrition on AutoOps SNS topic, to send notification by wechat.

## Install

```bash
MAIN_REGION=<main region>
cd ~/AutoOps/WechatNotify
STACK_NAME="AutoOps$(basename $(pwd))"
sam build && sam deploy --stack-name $STACK_NAME --region $MAIN_REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Uninstall

```bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $MAIN_REGION --no-cli-pager
```

