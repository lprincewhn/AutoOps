#!/bin/bash

REGIONS=()
PROFILE="default"
while [[ $# -gt 0 ]]; do
  case $1 in
    -r|--region)
      REGION="$2"
      shift # past argument
      shift # past value
      ;;
    -p|--profile)
      PROFILE="$2"
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
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      REGIONS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

echo "## Deploy AlarmProcessor in ${REGION}..."
sam build -t AlarmProcessor/template.yaml ${USE_CONTAINER}
sam deploy -t AlarmProcessor/template.yaml --stack-name AutoOpsAlarmProcessor --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM --profile $PROFILE

echo "## Deploy PhdEventProcessor in ${REGION}..."
sam build -t PhdEventProcessor/template.yaml ${USE_CONTAINER}
sam deploy -t PhdEventProcessor/template.yaml --stack-name AutoOpsPhdEventProcessor --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM --profile $PROFILE

echo "## Deploy EC2Provision in ${REGION}..."
sam build -t EC2Provision/template.yaml ${USE_CONTAINER}
sam deploy -t EC2Provision/template.yaml --stack-name AutoOpsEC2Provision --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM --profile $PROFILE

echo "## Deploy RDSProvision in ${REGION}..."
sam build -t RDSProvision/template.yaml ${USE_CONTAINER}
sam deploy -t RDSProvision/template.yaml --stack-name AutoOpsRDSProvision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM --profile $PROFILE

echo "## Deploy ESProvision in ${REGION}..."
sam build -t ESProvision/template.yaml ${USE_CONTAINER}
sam deploy -t ESProvision/template.yaml --stack-name AutoOpsESProvision --region $REGION --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM --profile $PROFILE

echo "## Deploy ASGEventProcessor in ${REGION}..."
sam build -t ASGEventProcessor/template.yaml ${USE_CONTAINER}
sam deploy -t ASGEventProcessor/template.yaml --stack-name AutoOpsASGEventProcessor --region $REGION --parameter-overrides SnsTopicArn=$SNS_TOPIC_ARN --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM --profile $PROFILE
