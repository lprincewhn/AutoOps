# AutoOps

This project contains useful operational processes represented as state machines with AWS StepFunctions. 

- [EBS Auto Scale](statemachine/EBSScaling)
- [EC2 Alarm Create](statemachine/EC2AlarmCreating)
- [Distribution Tag Update](statemachine/DistributionAutoTag)
- [EBS Tag Update](statemachine/EbsTagAutoUpdating)
- [ACM Certificate Expire Notification](statemachine/CertComplianceChk)

## How to deploy

0. Pick up state machines and generate the CloudFormation template
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

1. With SAM CLI installed
    ```
    # sam build
    # sam deploy --guided
    ```

2. Without SAM CLI, use CloudFormation template directly
    - Create a S3 bucket and prefix "AutoOps"
    ```
    # export your_bucket_name=<your-bucket-name>
    # aws s3 mb s3://${your_bucket_name}
    ```    
    - Upload the files in artifacts/ to s3://your-bucket-name/AutoOps. You need to replace "your-bucket-name" with your own S3 bucket name in following commands.
    ```
    # aws s3 sync ./artifacts s3://${your_bucket_name}/AutoOps
    ```
    - Modify the CloudFormation template packaged.yaml
        - Linux:
        ```
        # sed "s/<your S3 bucket>/${your_bucket_name}/g" packaged.yaml > packaged-out.yaml
        # aws s3 cp ./packaged-out.yaml s3://${your_bucket_name}/AutoOps/
        ```
        - MacOS:
        ```
        # sed "s/<your S3 bucket>/${your_bucket_name}/g" packaged.yaml > packaged-out.yaml
        # aws s3 cp ./packaged-out.yaml s3://${your_bucket_name}/AutoOps/
        ```
    - Run CloudFormation with packaged.yaml

## How to try

The state machines, who represent operational process, should be triggered by CloudWatch events. 

For testing or manually starting, a private API is also created so you can start execution of state machines by REST requests. If you want to do this, please create a VPC endpoint to Api Gateway service and modify Resource Policy of the API to allow invokation. You need to re-deploy the API after you modify its Resource Policy.

**Please be noted that you should apply other security service such as IAM authorization to protect this API.**








