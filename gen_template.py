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
Parameters:
  SnsTopicArn:
    Type: String
    Description: Enter SNS topic arn which notifications will send to.
    Default: ""
Conditions:
  BuildSnsTopicCondition: !Equals
    - !Ref SnsTopicArn
    - '' 
Resources:
  AutoOpsSnsTopic:
    Type: AWS::SNS::Topic
    Condition: BuildSnsTopicCondition
    Properties:
      TopicName: AutoOps
'''
tailer='''
Outputs:
  SNSTopic:
    Condition: BuildSnsTopicCondition
    Description: "SNS Topic notification will send to"
    Value: !Ref AutoOpsSnsTopic 
'''

statedirs = sys.argv[1:]

with open('template.yaml', 'w') as out:
    out.write(header)
    functions=set()
    ssmdocs=set()
    for statemachine in statedirs:
        with open(f'./{statemachine}/template.yaml') as fh:
            for line in fh:
                if line.strip().endswith('StateMachine:'):
                    tailer += f'''
  {line.strip()[:-1]}:
    Description: "ARN of {line.strip()[:-1]}"
    Value: !Ref {line.strip()[:-1]} 
'''
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
