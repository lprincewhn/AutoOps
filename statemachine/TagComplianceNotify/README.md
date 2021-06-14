# Tag Compliance Check

This state machine check tags of AWS resources periodly and notify users when tags are not compliant with users' reqirement.

[statemachine png]

## Trigger

Scheduled event from Cloudwatch. Defaultly it will do checking every day.

## Testing


```
# aws stepfunctions start-execution --state-machine-arn <value> --input <value>
```

## Parameters
1. TAGS_TO_CHECK, as an environment variable of lambda function 'TagCheck', it is a comma-seperated string to define all tags need to be checked.
