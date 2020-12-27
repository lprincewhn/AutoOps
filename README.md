# AutoOps

This project contains useful operational processes represented as state machines with AWS StepFunctions. 

- [EBS Auto Scale](statemachine/EBSScaling)
- [EC2 Alarm Create](statemachine/EC2AlarmCreating)
- [Distribution Tag Update](statemachine/DistributionAutoTag)
- [EBS Tag Update](statemachine/EbsTagAutoUpdating)
- [ACM Certificate Expire Notification](statemachine/CertComplianceChk)

## How to deploy

1. Start CloudShell

    ![https://console.aws.amazon.com/cloudshell/home]

2. Pick up state machines and generate the CloudFormation template
   
    ```
    # git clone https://github.com/lprincewhn/AutoOps.git
    # cd AutoOps/
    # python3 ./gen_template.py \
        statemachine/DistributionAutoTag/ \
        statemachine/EbsTagAutoUpdating/ \
        statemachine/EC2AlarmCreating/ \
        statemachine/EBSScaling/ \
        statemachine/CertComplianceChk/ \
    ```

3. Build and deply With SAM CLI
    ```
    # sam build
    # sam deploy --guided
    ```

## How to try

The state machines, who represent operational process, should be triggered by CloudWatch events. 

For testing or manually starting, a private API is also created so you can start execution of state machines by REST requests. If you want to do this, please create a VPC endpoint to Api Gateway service and modify Resource Policy of the API to allow invokation. You need to re-deploy the API after you modify its Resource Policy.

**Please be noted that you should apply other security service such as IAM authorization to protect this API.**








