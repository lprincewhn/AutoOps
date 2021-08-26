aws lambda update-function-configuration --function-name $1 --region $REGION --environment "{\"Variables\":$2}" --no-cli-pager
