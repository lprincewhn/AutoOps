# MergeMetricData

## Prerequisites

1. Create a bucket to store spill data of AthenaCloudwatchMetricsConnector.
2. Install AthenaCloudwatchMetricsConnector from SAR with recommended parameters as:
    - SpillBucket: The bucket name created above.
    - AthenaCatalogName: Athena data source name and federation query function name. And this same value will also be used to deploy this MergeMetricData stack.
    - SpillPrefix: Suggest the same value as AthenaCatalogName so you can install different athena connector with the same spill bucket.
3. Create database "default" in Glue if it does not exist.
4. Create a bucket in each region to store athena query results.  It will be used in parameter AthenaResultBucket. If there is one, this step can be skipped.
5. Create a bucket in the central region you picked to store metric data from all region.  It will be used in parameter MetricBucket.

## Trigger

Scheduled event from Cloudwatch. Defaultly it will do checking at 2:00AM UTC every day.

## Testing

```
# aws stepfunctions start-execution --state-machine-arn <MergeMetricDataStateMachine of stack output> --input '{"region":"<region>", "time":"<YYYY-MM-DD>"}'
```
 