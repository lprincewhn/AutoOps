#!/bin/bash

PROFILE=default
POSITIONAL_ARGS=()
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
    -f|--function-name)
      FUNCTION_NAME="$2"
      shift # past argument
      shift # past value
      ;;
    -p|--parameters)
      PARAMETERS="$2"
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

aws lambda update-function-configuration --function-name $FUNCTION_NAME --region $REGION --profile $PROFILE --environment "{\"Variables\":$PARAMETERS}" --no-cli-pager
