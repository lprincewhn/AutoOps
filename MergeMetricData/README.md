# MergeMetricData

## Prerequisites

1. Create a bucket to store spill data of AthenaCloudwatchMetricsConnector.
2. Install AthenaCloudwatchMetricsConnector from SAR with recommended parameters as:
    - SpillBucket: The bucket name created above.
    - AthenaCatalogName: Athena data source name and federation query function name. And this same value will also be used to deploy this AutoOpsCentMetricDB stack.
    - SpillPrefix: Suggest the same value as AthenaCatalogName so you can install different athena connector with the same spill bucket.
3. Create database "default" in Glue if it does not exist.
4. Create a bucket in each region to store athena query results.  It will be used in parameter AthenaResultBucket. If there is one, this step can be skipped.
5. Create a bucket in the central region you picked to store metric data from all region.  It will be used in parameter MetricBucket.

## Deploy the home region

```bash
AWS_REGION=<Home region>
METRIC_DATA_BUCKET=<Bucket to store metric data from all region>
sam build --template-file ./template-home.yaml && sam deploy --template-file ./template-home.yaml --stack-name AutoOpsCentMetricDB --region $AWS_REGION --parameter-overrides CmdbBucket=${METRIC_DATA_BUCKET} --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Deploy the guess region
```bash
AWS_REGION=<Guess region>
ATHENA_CATALOG_NAME=<AthenaCatalogName>
ATHENA_RESULT_BUCKET=<Athea query result bucket>
sam build --template-file ./template-guress.yaml && sam deploy --template-file ./template-guess.yaml --stack-name AutoOpsRegionMetricDB --region $AWS_REGION --parameter-overrides AthenaCatalogName=${ATHENA_CATALOG_NAME} CmdbBucket=${CMDB_BUCKET} --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Trigger

Scheduled event from Cloudwatch. Defaultly it will do checking at 2:00AM UTC every day.

## Testing

```
# aws stepfunctions start-execution --state-machine-arn <MergeMetricDataStateMachine of stack output> --input '{"region":"<region>", "time":"<YYYY-MM-DD>"}'
```
 