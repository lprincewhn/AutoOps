#  Transform and deliver Redshift audit logs in S3 bucket to Amazon ElasticSearch service

* Following command are for AWSCLIv2, if you are using v1, please remove the --no-cli-pager option.

## Deploy 

1. Deploy with SAM CLI

```
# cd ~/AutoOps/RedshiftAuditLogToES
# REGION=<region>
# SourceBucket=<S3 bucket storing cloudfront standard log>
# DestinationESArn=<ARN of AES domain>
# DestinationBucket=<S3 bucket for backup>
# sam build
# sam deploy --stack-name RedshiftAuditLogToES --region $REGION --parameter-overrides SourceBucket=$SourceBucket DestinationESArn=$DestinationESArn DestinationBucket=$DestinationBucket --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

2. Add S3 trigger to RedshiftAuditLogTransformFunction

3. Map role FirehoseRole in AES if finegrained access control is enabled.