# Create resource group according tags

Check and create resource group according tags every day.

* Following command are for AWSCLIv2, if you are using v1, please remove the --no-cli-pager option.

## Deploy 

```
# cd ~/AutoOps/ResourceGroupProvision
# REGION=<region>
# sam build
# sam deploy --stack-name AutoOpsRGProvision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Start

```
# STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsRGProvision --region $REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`RGProvisionStateMachineArn`].OutputValue' --output text)
# aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --region $REGION --no-cli-pager
```

## Config

Set value of following parameters according your requirement:

1. Parameters of CreateResourceGroupFunction
- TAG_KEYS: Tag keys separated by comma, resource group will be created for each distinct value of each tag key.

## Uninstall

```
# aws cloudformation delete-stack --stack-name AutoOpsPhdEventProcessor --region $REGION --no-cli-pager
```

## Limitation

* Because resource group name only can include alphanumeric characters, tag key and value with other characters will be ignored.