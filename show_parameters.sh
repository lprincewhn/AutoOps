FUNCTIONS=( $(aws cloudformation describe-stack-resources --region $REGION --stack-name $1 --query "StackResources[?ResourceType=='AWS::Lambda::Function'].PhysicalResourceId" --output text) )
for f in $FUNCTIONS
do
  echo $f
  aws lambda get-function --region $REGION --function-name $f --query "Configuration.Environment.Variables" --no-cli-pager
done
