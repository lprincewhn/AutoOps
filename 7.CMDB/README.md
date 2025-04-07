# CMDB

## Prerequisites

1. Create a bucket to store spill data of AthenaAwsCmdbConnector.
2. Install AthenaAwsCmdbConnector from SAR in each guess region with recommended parameters as:
    - SpillBucket: The bucket name created above.
    - AthenaCatalogName: Athena data source name and federation query function name. And this same value will also be used to deploy this stack.
    - SpillPrefix: Suggest the same value as AthenaCatalogName so that you can install different athena connector in the same spill bucket.
3. Create database "default" in Glue if it does not exist.
4. Create a bucket in each region to store athena query results.  It will be used in parameter AthenaResultBucket. If there is one, this step can be skipped.
5. Create a bucket in the central region you picked to store CMDB data from all region.  It will be used in parameter CmdbBucket.

## Deploy in the guess region

**Note: Should be used if in guest regions which store regional CMDB data into the S3 bucket in home region**

```
STACK_NAME=AutoOpsCMDB
AWS_REGION=us-east-1
ATHENA_CATALOG_NAME=aws-cmdb
CMDB_BUCKET=cmdb.597377428377
sam build --template ./template-guess.yaml && sam deploy --stack-name $STACK_NAME --region $AWS_REGION \
    --parameter-overrides AthenaCatalogName=${ATHENA_CATALOG_NAME} CmdbBucket=${CMDB_BUCKET} \
    --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

```
# MAIN_REGION=us-east-1
# ATHENA_RESULT_BUCKET=athena-result.virginia.597377428377
# CMDB_BUCKET=cmdb.597377428377
# sam build --template ./centric_template.yaml
# sam deploy --stack-name AutoOpsCentricCmdb --region $MAIN_REGION --parameter-overrides CmdbBucket=${CMDB_BUCKET} --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```

## Trigger

Scheduled event from Cloudwatch. Defaultly it will do checking at 2:00AM UTC every day.

## Testing

```
# aws stepfunctions start-execution --state-machine-arn <MergeCmdbDataStateMachine of stack output> --input '{"region":"<region>", "time":"<YYYY-MM-DD>"}'
```
 
