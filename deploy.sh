REGIONS=(us-east-1)
cd EC2Provision
for REGION in ${REGIONS}
do
  sam build --use-container
  sam deploy --stack-name AutoOpsEC2Provision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM
done
cd ..
