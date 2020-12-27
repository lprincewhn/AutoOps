import re
import sys
import json

header='''
AWSTemplateFormatVersion: "2010-09-09"
Transform: AWS::Serverless-2016-10-31
Description: >
  AutoOps contains useful operational processes represented as a state machines with AWS StepFunctions.
Metadata:
  AWS::ServerlessRepo::Application:
    Name: AutoOps
    Description: A toolkit for auto ops in AWS.
    Author: whuaning
    SpdxLicenseId: Apache-2.0
    ReadmeUrl: README.md
    SemanticVersion: 0.0.1
Resources:
  AutoOpsApiGateway:
    Type: AWS::Serverless::Api
    Properties:
      StageName: Prod
      EndpointConfiguration: PRIVATE
      Auth:
        ResourcePolicy:
          CustomStatements: [{
                              "Effect": "Allow",
                              "Principal": "*",
                              "Action": "execute-api:Invoke",
                              "Resource": "execute-api:/Prod/*",
                              "Condition": {
                                "IpAddress": {
                                  "aws:VpcSourceIp": "172.31.0.0/16"
                                }
                              }
                            }]        
  AutoOpsSnsTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: AutoOps
'''
tailer='''
Outputs:
  APIEndpoint:
    Description: "APIGateway Endpoint to start status machines' execution"
    Value: !Join ["/", ["https:", "", !Join [".", [!Ref AutoOpsApiGateway, "execute-api", !Ref AWS::Region, "amazonaws.com"]], !Ref AutoOpsApiGatewayProdStage]]
'''

statedirs = sys.argv[1:]

with open('template.yaml', 'w') as out:
    out.write(header)
    functions=set()
    ssmdocs=set()
    for statemachine in statedirs:
        with open(f'./{statemachine}/template.yaml') as fh:
            for line in fh:
                out.write(line)
                functions = functions.union(re.findall(r"[!GetAtt|!Ref] (.+)Function",line))
            print(f'Added {statemachine}/template.yaml')
        out.write('\n')
    for func in functions:
        with open(f'./functions/{func}/template.yaml') as fh:
            for line in fh:
                out.write(line)
                ssmdocs = ssmdocs.union(re.findall(r"[!GetAtt|!Ref] (.+)Doc",line))
            print(f'Added ./functions/{func}/template.yaml')
        out.write('\n')
    for doc in ssmdocs:
        with open(f'./ssmdocuments/{doc}/template.yaml') as fh:
            for line in fh:
                out.write(line)
            print(f'Added ./ssmdocuments/{doc}/template.yaml')
        out.write('\n')
    out.write(tailer)
