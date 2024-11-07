# CloudTrailEvents

## Prerequisites

1. Create CloudTrail trail and store to S3 bucket.
2. Enable EventBridge notification for S3 bucket 
3. Create EventBus

## Deploy
```bash
AWS_REGION=us-east-1
CLOUDTRAIL_BUCKET=athena-result.virginia.597377428377
EVENT_BUS_NAME=AutoOpsEvent
sam build && sam deploy --stack-name AutoOpsCloudTrailEvents --region $AWS_REGION --parameter-overrides EventBusName=${EVENT_BUS_NAME} CloudTrailBucket=${CLOUDTRAIL_BUCKET} --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```
