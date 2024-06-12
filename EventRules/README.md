# EventRules

- State machine to create/delete alarms.

**Commands in this document are for [AWSCLIv2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html). You can excecute them in [CloudShell](https://console.aws.amazon.com/cloudshell), in which these tools have been installed.**

## Deploy with target SNS topic

**Note: Should be used in home region which will process the notifications**

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/EventRules
AUTO_OPS_TOPIC=<SNS topic receive AutoOps notification> # Messages of this topic will be sent by StepFunction or Lambda, should be in the home region
AWS_REGION=<region>
STACK_NAME="AutoOps$(basename $(pwd))"
sam build --template-file ./template-home.yaml && sam deploy --template-file ./template-home.yaml --stack-name $STACK_NAME --region $AWS_REGION \
    --parameter-overrides CloudWatchAlarmTargetArn=$AUTO_OPS_TOPIC EC2InstanceStateTargetArn=$AUTO_OPS_TOPIC HealthEventTargetArn=$AUTO_OPS_TOPIC \
    --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Deploy with targets of home region'e EventBridge bus

**Note: Should be used if in guest regions which cannot process the notifications**

``` bash
git clone https://github.com/lprincewhn/AutoOps.git
cd ~/AutoOps/EventRules
HOME_REGION_BUS="arn:aws:events:us-east-1:597377428377:event-bus/default"
AWS_REGION=<region>
STACK_NAME="AutoOps$(basename $(pwd))"
sam build --template-file ./template-guess.yaml && sam deploy --template-file ./template-guess.yaml --stack-name $STACK_NAME --region $AWS_REGION \
    --parameter-overrides HomeDefaultBusArn=$HOME_REGION_BUS \
    --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```


## Uninsatll
``` bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $AWS_REGION --no-cli-pager
```