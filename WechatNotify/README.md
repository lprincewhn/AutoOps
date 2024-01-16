# Notification by wechat

This will create an lambda subscrition on AutoOps SNS topic, to send notification by wechat.

## Install

```bash
AWS_REGION=<main region>
cd ~/AutoOps/WechatNotify
STACK_NAME="AutoOps$(basename $(pwd))"
sam build && sam deploy --stack-name $STACK_NAME --region $AWS_REGION --parameter-overrides SnsTopicArn=$AUTO_OPS_TOPIC --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Uninstall

```bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```


1. 创建Topic (AutoOpsCommon)
```bash
aws sns create-topic 
```
2. 创建EventBridge规则
```bash
# Input Path
{
  "alarmName": "$.detail.alarmName",
  "description": "$.detail.configuration.description",
  "state": "$.detail.state.value"
}

# Input Template - Json
{
  "state": <state>,
  "alarmName": <alarmName>,
  "description": <description>
}

# Input Tempalte - Text
"【<state>】<alarmName>\n<description>"


aws events put-rule --name PHD-Notification --event-pattern '{"source": ["aws.health"],"detail-type": ["AWS Health Event"]}' --no-cli-pager --query
aws events put-targets --rule PHD-Notification --targets '[{"Id":"sns_topic","Arn":"arn:aws:sns:us-east-1:597377428377:AutoOps"}]' --no-cli-pager
```

3. 创建其他区域的EventBridge规则