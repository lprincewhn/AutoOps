#!/bin/bash

REGIONS=()
PROFILE="default"
while [[ $# -gt 0 ]]; do
  case $1 in
    -m|--main-region)
      MAIN_REGION="$2"
      shift # past argument
      shift # past value
      ;;
    -c|--use-container)
      USE_CONTAINER="--use-container"
      shift # past argument
      ;;
    -t|--sns-topic-arn)
      SNS_TOPIC_ARN="$2"
      shift # past argument
      shift # past value
      ;;
    -p|--profile)
      PROFIlE="$2"
      shift # past argument
      shift # past value
      ;;
    -*|--*)
      echo "Error: Unknown option $1."
      exit 1
      ;;
    *)
      REGIONS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

if [ ! -n "${MAIN_REGION}${SNS_TOPIC_ARN}" ]; then
  echo "Error: At least 1 of --main-region and --sns-topic-arn should be set."
  exit 1
fi

if [ -n "${MAIN_REGION}" ];
then
  echo "## Deploy common components in main_region ${MAIN_REGION}..."
  cd Common/
  sam build ${USE_CONTAINER}
  sam deploy --stack-name AutoOpsCommon --region ${MAIN_REGION} --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM --profile ${PROFILE}
  SNS_TOPIC_ARN=$(aws cloudformation describe-stacks --stack-name AutoOpsCommon --region $MAIN_REGION --no-cli-pager --query 'Stacks[0].Outputs[?OutputKey==`SNSTopic`].OutputValue' --output text --profile $PROFILE)
  cd ..
fi

for REGION in ${REGIONS[*]}
do
  echo "## Deploy ${REGION}..."
  zsh deploy_region.sh --region $REGION --profile $PROFILE --sns-topic-arn $SNS_TOPIC_ARN --use-container
done
