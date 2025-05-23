# 0. EventRules

Create AWS EventBridge rules to forward ops events.

**Commands in this document are for [AWSCLIv2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). You can excecute them in [CloudShell](https://console.aws.amazon.com/cloudshell), in which these tools have been installed.**

## Ops event flow

### Option 1: Only for notification for cloudwatch alarm or events

```mermaid
flowchart TD
	PHD["Health Events"] --> EventBridgeSelfManaged;
    CloudWatch["CloudWatch Alarm"] --> EventBridgeSelfManaged;
    AutoOps["Customized AutoOps Events"] --> EventBridgeSelfManaged;
    EventBridgeSelfManaged --> EventBridgeUserNotification;
    EventBridgeUserNotification --> |User Notification Rule|ChatBot;
	EventBridgeSelfManaged --> |optional: format text message|SNS;
	EventBridgeSelfManaged --> StepFunction["AutoOps workflow"];
	SNS --> Lambda["Text Notification Lambda"];
	ChatBot --> Chime/Slack/Teams;
	Lambda --> Wechat/Wecom/Feishu/Dingding;
```

### Option 2: Integrate with AWS System Manager Incident Manager for cloudwatch alarm

```mermaid
flowchart TD
    CloudWatch["CloudWatch Alarm"] --> OpsItem;
    OpsItem --> |Manually start|Incident;
    Incident --> |format ChatBot message|SNS;
	SNS --> |ChatBot message only|ChatBot;
	SNS --> Lambda["Text Notification Lambda"];
	ChatBot --> Chime/Slack/Teams;
	Lambda --> Wechat/Wecom/Feishu/Dingding;
	Incident --> EventBridge;
	EventBridge --> |format text message|SNS;
	EventBridge --> StepFunction["AutoOps workflow"];
```

```mermaid
flowchart TD
    CloudWatch["CloudWatch Alarm"] --> Incident;
    Incident --> |Auto create|OpsItem;
    Incident --> |format ChatBot message|SNS;
	SNS --> |ChatBot message only|ChatBot;
	SNS --> Lambda["Text Notification Lambda"];
	ChatBot --> Chime/Slack/Teams;
	Lambda --> Wechat/Wecom/Feishu/Dingding;
	Incident --> EventBridge;
	EventBridge --> |format text message|SNS;
	EventBridge --> StepFunction["AutoOps workflow"];
```

## Deploy in the home region

If the event rule target is SNS topic, below access policy need to be added in the SNS topic. Ref: https://docs.aws.amazon.com/zh_cn/eventbridge/latest/userguide/eb-troubleshooting.html#eb-no-messages-published-sns

```json
    {
      "Sid": "AWSEvents_test_Id415febb3-bdc2-4888-a347-1699adbda1d7",
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sns:Publish",
      "Resource": "<SNS topic receive AutoOps notification>"
    }
```
**Note: Should be used in home region which processes the events centrally.**

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/0.EventRules
AUTO_OPS_TOPIC=<SNS topic receive AutoOps notification> # Messages of this topic will be sent by StepFunction or Lambda, should be in the home region
AWS_REGION=<Home region>
STACK_NAME="AutoOpsEventRules"
sam build --template-file ./template-home.yaml && sam deploy --template-file ./template-home.yaml --stack-name $STACK_NAME --region $AWS_REGION \
    --parameter-overrides AutoOpsEventTargetArn=$AUTO_OPS_TOPIC  \
    --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

If events from other account needs to be forward by the home region event bus, a resource-based permission policy needs to by added.

## Deploy in the guess region

**Note: Should be used if in guest regions which forward the events to the home region**

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/0.EventRules
HOME_REGION_BUS=<Eventbus arn in home region>
AWS_REGION=<Guess region>
STACK_NAME="AutoOpsEventRules"
sam build --template-file ./template-guess.yaml && sam deploy --template-file ./template-guess.yaml --stack-name $STACK_NAME --region $AWS_REGION \
    --parameter-overrides HomeDefaultBusArn=$HOME_REGION_BUS \
    --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```


## Uninsatll
``` bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```