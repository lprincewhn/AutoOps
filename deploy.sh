cd Common/
MAIN_REGION=us-east-1
sam build
sam deploy --stack-name AutoOpsCommon --region $MAIN_REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
SNS_TOPIC_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsCommon --region $MAIN_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`SNSTopic`].OutputValue' --output text)
cd ..

REGIONS=(us-east-1)
cd AlarmProcessor
for REGION in ${REGIONS}
do 
  sam build
  sam deploy --stack-name AutoOpsAlarmProcessor --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
done
cd ..
cd EC2Provision
for REGION in ${REGIONS}
do
  sam build
  sam deploy --stack-name AutoOpsEC2Provision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
done
cd ..
cd RDSProvision
for REGION in ${REGIONS}
do
  sam build
  sam deploy --stack-name AutoOpsRDSProvision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
done
cd ..
cd ESProvision
for REGION in ${REGIONS}
do
  sam build
  sam deploy --stack-name AutoOpsESProvision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
done
cd ..
