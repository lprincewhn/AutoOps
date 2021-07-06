for i in $(aws ec2 describe-instances --query 'Reservations[].Instances[].InstanceId' --no-cli-pager --region ${REGION} --output text)
do
  aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --input "{\"detail\": {\"instance-id\": \"${i}\",\"state\": \"running\"}}" --no-cli-pager --region ${REGION} 
  sleep 60
done
   
