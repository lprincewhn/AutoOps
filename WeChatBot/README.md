# WeChatBot

This is a Wechat/WeCom Bot leveraging AWS Bedrock and other service capabilities to support OPS engineer.


## Prerequisite
Provison your WeChat/WeCom account with:
1. Sign up a WeCom account and get your "Company ID", which is referred as variable "corpid" below.
https://work.weixin.qq.com/wework_admin/register_wx?from=myhome
2. Prepare and configure your company domain name in your WeCom account.
https://work.weixin.qq.com/wework_admin/frame#profile/domain
3. Create an APP in your WeCom account and get its "AgentId" and "Secret", which are referred as varialbes "agentid" and "corpsecret" below.
https://work.weixin.qq.com/wework_admin/frame#apps/createApiApp
4. To secure your bot appliation by limiting the client IP, you need to get the WeCom server IP list.
https://developer.work.weixin.qq.com/document/path/90238#%E8%8E%B7%E5%8F%96%E4%BC%81%E4%B8%9A%E5%BE%AE%E4%BF%A1%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%9A%84ip%E6%AE%B5

    The server IP list can be got by following commands:
    ``` bash
    # Get access token
    curl -X POST 'https://qyapi.weixin.qq.com/cgi-bin/gettoken' -d '{"corpid":"<corpid>","corpsecret":"<corpsecret>"}' -s # <corpid> and <corpsecret> are from step 1,3
    # Get IP server list
    curl 'https://qyapi.weixin.qq.com/cgi-bin/getcallbackip?access_token=<access token>' -s # <access token> is from above output
    ```

5. Prepare an SNS topic in your AWS account to send message to WeChat/WeCom.
6. Apply or upload SSL certificate of the APP domain name in AWS Certificate Manager.
7. Prepare an APP domian name belonging your company domain, Token and EncodingAESKey strings to receive the WeChat/WeCom messages.
8. Configure APP domain name URL, Token and EncodingAESKey strings in the created APP. Token and EncodingAESKey strings, which are referred as "bottoken" and "botaeskey" below, are used to encryt the message.

## Install

```bash
REGION=<region>
IP_WHITE_LIST=<WeCom server IP list> # From #Prerequisite step 4
AUTO_OPS_TOPIC=<SNS topic ARN> # From #Prerequisite step 5
DOMAIN_CERT_ARN=<WeCom APP domain certificate ARN> # From #Prerequisite step 6
DOMAIN_NAME=<WeCom APP domain name> # From #Prerequisite step 8
cd ~/AutoOps/WeChatBot
STACK_NAME="AutoOps$(basename $(pwd))"
sam build && sam deploy --stack-name $STACK_NAME --region $REGION --parameter-overrides DomainName=$DOMAIN_NAME DomainCertificateArn=$DOMAIN_CERT_ARN AllowedIPList=$IP_WHITE_LIST SnsTopicArn=$AUTO_OPS_TOPIC --confirm-changeset --resolve-s3 --capabilities CAPABILITY_IAM

# Following commands are also in the CloudFormation stack output
# Update wechat secret
aws secretsmanager put-secret-value --region $REGION --secret-id <the secret arn> --secret-string '{"corpid":"<corpid>","corpsecret":"<corpsecret>","agentid":"<agentid>","bottoken":"<bottoken>","botaeskey":"<botaeskey>"}' # From #Prerequisite step 1,3,8
# Enable event source of Lambda
aws lambda update-event-source-mapping --region $REGION --function-name <lambda function name> --uuid <lambda event source uuid> --enabled
```

Then, you need to update your DNS record to resolve the DomainName to BotApiGatewayEndpoint.


## Uninstall

```bash
aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION --no-cli-pager
```