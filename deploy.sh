cd Common/
MAIN_REGION=us-east-1
sam build
sam deploy --stack-name AutoOpsCommon --region $MAIN_REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
SNS_TOPIC_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsCommon --region $MAIN_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`SNSTopic`].OutputValue' --output text)
cd ..

REGIONS=(us-east-1 us-east-2)
for REGION in ${REGIONS}
do
  zsh deploy_region_with_container.sh $REGION $SNS_TOPIC_ARN
done
