import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    eventOut = {
        "accountId": event["account"],
        "region": event["region"],
        "time": event["time"],
        "finding_type": event["detail"]["type"],
        "resource_type": event["detail"]["resource"]["resourceType"]
    }    
    if eventOut["resource_type"] == 'Instance':
        eventOut["instanceId"] = event["detail"]["resource"]["instanceDetails"]["instanceId"]
        eventOut["tags"] =  event["detail"]["resource"]["tags"]
    if eventOut["resource_type"] in ['Backdoor:EC2/C&CActivity.B!DNS']:
        eventOut["domain"] = event["detail"]["service"]["action"]["dnsRequestAction"]["domain"]
        eventOut["description"] = event["detail"]["description"]
    print(f'Event Out: {eventOut}')
    return eventOut

