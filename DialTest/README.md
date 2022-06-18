# Transform and deliver CloudFront standard logs in S3 bucket to Cloudwatch or Amazon OpenSearch service.

![](doc/VisualizeCloudFrontLog.png)

* Following command are for AWSCLIv2, if you are using v1, please remove the --no-cli-pager option.

## Deploy 

1. Deploy with SAM CLI

``` bash
cd ~/AutoOps/DialTest
REGION=<region>
DestinationESArn=<ARN of AES domain>
sam build
sam deploy --stack-name AutoOpsDialTest --region $REGION --parameter-overrides CloudFrontServiceTimingPolicyId=$CloudFrontServiceTimingPolicyId DialTarget=$DialTarget --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

2. Map role FirehoseRole in AES if finegrained access control is enabled.
