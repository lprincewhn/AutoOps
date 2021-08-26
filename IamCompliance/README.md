# Process non-compliant resource in AWS Config and send notifications

Deploy rule of AWS Config to check IAM compliance.

* Following aws commands are for AWSCLIv2, if you are using v1, please remove the --no-cli-pager option.

## Prerequisites

Set-up AWS Config in regions. For global resources, only need to be included in one region.

https://docs.aws.amazon.com/zh_cn/config/latest/developerguide/gs-console.html

## Deploy 

```
# REGION=<region>
# sam build
# sam deploy --stack-name AutoOpsIamCompliance --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Config

Set value of following parameters according your requirement:

1. Parameters of IamUserComplianceConfigRule
- requiredGroupList: IAM group names separated by comma which IAM users should be in.
- exemptedUserList: IAM users which are exempted in compliance check.

## Uninstall

```
# aws cloudformation delete-stack --stack-name AutoOpsIamCompliance --region $REGION --no-cli-pager
```
