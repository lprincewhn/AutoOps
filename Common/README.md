# Common Resources 

Following commint resource will be installed in your AWS account:
- SNS Topic: Notifications will be sent to this topic
- S3 Bucket: This bucket will store CloudTrail events 
- CloudTrail: A cloudtrail to monitor management events from all regions

## Install 

```
# MAIN_REGION=<main region>
# cd ~/AutoOps/Common
# sam build
# sam deploy --stack-name AutoOpsCommon --region $MAIN_REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Uninstall

```
# aws cloudformation delete-stack --stack-name AutoOpsCommon --region $MAIN_REGION --no-cli-pager
```
