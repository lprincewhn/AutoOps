REGION=$1
SNS_TOPIC_ARN=$2

sam build -t AlarmProcessor/template.yaml --use-container
sam deploy -t AlarmProcessor/template.yaml --stack-name AutoOpsAlarmProcessor --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM

sam build -t PhdEventProcessor/template.yaml --use-container
sam deploy -t PhdEventProcessor/template.yaml --stack-name AutoOpsPhdEventProcessor --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM

sam build -t EC2Provision/template.yaml --use-container
sam deploy -t EC2Provision/template.yaml --stack-name AutoOpsEC2Provision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM

sam build -t RDSProvision/template.yaml --use-container
sam deploy -t RDSProvision/template.yaml --stack-name AutoOpsRDSProvision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM

sam build -t ESProvision/template.yaml --use-container
sam deploy -t ESProvision/template.yaml --stack-name AutoOpsESProvision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM

sam build -t ASGEventProcessor/template.yaml --use-container
sam deploy -t ASGEventProcessor/template.yaml --stack-name AutoOpsASGEventProcessor --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
