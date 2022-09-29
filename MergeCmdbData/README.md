# MergeCmdbData

## Prerequisites

1. Create a bucket to store spill data of AthenaAwsCmdbConnector.
2. Install AthenaAwsCmdbConnector from SAR with recommended parameters as:
    - SpillBucket: The bucket name created above.
    - AthenaCatalogName: Athena data source name and federation query function name. And this same value will also be used to deploy this MergeCmdbData stack.
    - SpillPrefix: Suggest the same value as AthenaCatalogName so that you can install different athena connector in the same spill bucket.
3. Create database "default" in Glue if it does not exist.
4. Create a bucket in each region to store athena query results.  It will be used in parameter AthenaResultBucket. If there is one, this step can be skipped.
5. Create a bucket in the central region you picked to store CMDB data from all region.  It will be used in parameter CmdbBucket.

## Deploy

```
# MAIN_REGION=us-east-1
# CMDB_BUCKET=cmdb.597377428377
# sam build --template ./centric_template.yaml
# sam deploy --stack-name AutoOpsCentricCmdb --region $MAIN_REGION --parameter-overrides CmdbBucket=${CMDB_BUCKET} --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
# REGION=us-east-1
# ATHENA_CATALOG_NAME=aws-cmdb
# ATHENA_RESULT_BUCKET=athena-result.virginia.597377428377
# sam build --template ./region_template.yaml
# sam deploy --stack-name AutoOpsRegionCmdb --region $REGION --parameter-overrides AthenaCatalogName=${ATHENA_CATALOG_NAME} CmdbBucket=${CMDB_BUCKET} --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
```
## Trigger

Scheduled event from Cloudwatch. Defaultly it will do checking at 2:00AM UTC every day.

## Testing

```
# aws stepfunctions start-execution --state-machine-arn <MergeCmdbDataStateMachine of stack output> --input '{"region":"<region>", "time":"<YYYY-MM-DD>"}'
```
 
