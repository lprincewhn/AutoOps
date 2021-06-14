# EC2 Alarm Create

- State machine to put disk alarms when EC2 instances go running

    ![](../../doc/ec2alarm_autocreating.asl.png)

This state machine creates EBS usage alarms when EC2 instances starts.

## Testing

1. EC2 disk arlam auto-creating

    ```
    # curl <APIGateway Endpoint>/ec2_alarm_create -X POST -d '{"input": "{\"detail-type\": \"EC2 Instance State-change Notification\", \"source\": \"aws.ec2\", \"detail\": {\"instance-id\": \"<Your EC2 Instance ID for test>\", \"state\": \"running\"}}","stateMachineArn": "<EC2 disk alarm auto-creating state machine ARN>"}'
    ```

    For Linux instance, CloudWatch event rules will be created for each ebs attached to this instance. The alarm threshold is 80% by default. If you want to change the threshold, please update Environment of Lambda function CreateLinuxDiskAlarms.

    For Windows instance, CloudWatch event rules will be created for each ebs attached to this instance. The alarm threshold is 20% by default. If you want to change the threshold, please update Environment of Lambda function CreateWindowsDiskAlarms.