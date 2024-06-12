for i in $(aws ec2 describe-instances --query 'Reservations[].Instances[].InstanceId' --no-cli-pager --region ${REGION} --output text)
do
  aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --input "{\"account\":\"${account}\",\"region\":\"${REGION}\",\"time\":\"2021-09-22T06:00:43Z\",\"detail\": {\"instance-id\": \"${i}\",\"state\": \"running\"}}" --no-cli-pager --region ${REGION} 
  sleep 20
done
   
