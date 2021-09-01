for i in $(aws rds describe-db-instances --query "DBInstances[?Engine=='mysql'].DBInstanceIdentifier" --no-cli-pager --no-cli-pager --region ${REGION} --output text)
do
  aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --input "{\"detail\": {\"SourceIdentifier\": \"${i}\",\"EventID\": \"RDS-EVENT-0005\"}}" --no-cli-pager --region ${REGION} 
  sleep 60
done
   
