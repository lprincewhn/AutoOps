# Notification by wechat

This will create an lambda subscrition on AutoOps SNS topic, to send notification by wechat.

## Install

```
# MAIN_REGION=<main region>
# cd ~/AutoOps/WechatNotify
# sam build
# sam deploy --stack-name AutoOpsWechatNotify --region $MAIN_REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Uninstall

```
# aws cloudformation delete-stack --stack-name AutoOpsWechatNotify --region $MAIN_REGION --no-cli-pager
```

