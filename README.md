# AutoOps

This project contains useful operational processes represented as state machines with AWS StepFunctions. 

![](doc/AutoOps.png)

## How to deploy

You can pickup one region to deploy SNS topic 

1. Start CloudShell and clone this project

    ![https://console.aws.amazon.com/cloudshell/home]

    ```
    # cd ~
    # git clone https://github.com/lprincewhn/AutoOps.git
    ```

2. Pick up a main region to deploy a common SNS topic where notification will be sent to, or you can use an SNS topic existed by setting it in environment variable $SNS_TOPIC_ARN.
   
    ```
    # MAIN_REGION=<main region>
    # cd ~/AutoOps/Common/
    # sam build
    # sam deploy --stack-name AutoOpsCommon --region $MAIN_REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
    ```

3. Go into sub directory of each process to continue.

- [EC2Provision](EC2Provision): Create/Delete alarms for EC2 instances when they are started/terminated.
- [RDSProvision](RDSProvision): Create/Delete alarms for RDS database nodes when they are started/terminated.
- [ESProvision](ESProvision): Deploy CloudWatch alarms for AWS Elasticsearch domain
- [CloudFrontProvision](CloudFrontProvision): Deploy CloudWatch alarms for AWS CloudFront distribution
- [AlarmNotify](AlarmNotify): Process CloudWatch alarms and send notifications
- [MergeMetricData](MergeMetricData): Merge CloudWatch metric data to to centralized S3 bucket
- [SecurityHarden](SecurityHarden): Harden security by AWS Guardduty

## How to try

The state machines, who represent operational processes, should be triggered by CloudWatch events (for AWS resource) or API Gateway (for external resource). And you can use awscli command to start state machines' execution.


