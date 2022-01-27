#!/bin/bash

POSITIONAL_ARGS=()
PROFILE=default
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
    -s|--stack-name)
      STACK_NAME="$2"
      shift # past argument
      shift # past value
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

FUNCTIONS=( $(aws cloudformation describe-stack-resources --region $REGION --profile $PROFILE --stack-name $STACK_NAME --query "StackResources[?ResourceType=='AWS::Lambda::Function'].PhysicalResourceId" --output text) )
for f in ${FUNCTIONS[*]}
do
  echo $f
  aws lambda get-function --region $REGION --profile $PROFILE --function-name $f --query "Configuration.Environment.Variables" --no-cli-pager
done
