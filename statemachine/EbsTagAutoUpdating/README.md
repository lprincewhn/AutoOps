# EBS Tag Update

This state machine update EBS tags with EC2 tags  when EC2 instances starts.

## Mannully running

1. Tag 1 EC2 instance's EBS

```
# REGION=us-east-1
# InstanceId=i-xxxxxxxx
# STATE_MACHINE_ARN=`aws cloudformation describe-stacks --region ${REGION} --stack-name AutoOps --query "Stacks[].Outputs[?OutputKey=='EbsTagUpdatingStateMachine'].OutputValue" --output text`
# aws stepfunctions start-execution --region ${REGION} --state-machine-arn ${STATE_MACHINE_ARN} --input '{"detail": {"instance-id": ${InstanceId},"state": "running"}}' 
```

2. Tag all EC2 instances' EBS

```
# REGION=us-east-1
# STATE_MACHINE_ARN=`aws cloudformation describe-stacks --region ${REGION} --stack-name AutoOps --query "Stacks[].Outputs[?OutputKey=='EbsTagUpdatingStateMachine'].OutputValue" --output text`
# for i in `aws ec2 describe-instances --query "Reservations[].Instances[].InstanceId" --output text`; do aws stepfunctions start-execution --region ${REGION} --state-machine-arn ${STATE_MACHINE_ARN} --input "{\"detail\": {\"instance-id\": \"${i}\",\"state\": \"running\"}}" --no-cli-pager; done
```
