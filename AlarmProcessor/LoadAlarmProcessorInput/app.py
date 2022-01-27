import json
import datetime

import json
import datetime

def lambda_handler(event, context):
    print(f'Event In: {event}')
    alarmName = event["detail"]["alarmName"]
    beijing_time = datetime.datetime.strptime(event["time"], '%Y-%m-%dT%H:%M:%SZ').astimezone(tz =datetime.timezone(datetime.timedelta(hours=8)))
    metrics = event["detail"]["configuration"]["metrics"]
    currentState = event["detail"]["state"]["value"]
    previousState = event["detail"]["previousState"]["value"]
    reason = event["detail"]["state"]["reason"]
    reasonData = event["detail"]["state"].get("reasonData")
    recentDatapoints = json.loads(reasonData)["recentDatapoints"] if reasonData else ''
    print(f'ReasonData: {reasonData}')
    eventOut = {
        'account': event['account'],
        'region': event['region'],
        'alarmName': alarmName, 
        'timestamp': datetime.datetime.strftime(beijing_time, '%Y-%m-%dT%H:%M:%S+0800'), 
        'time': datetime.datetime.strftime(beijing_time, '%H:%M:%S'),
        'objectType': alarmName.split('-')[0], 
        'metrics': metrics, 
        'currentState': currentState,
        'previousState': previousState, 
        'reason': reason,
        'eventData': json.dumps(event)
    }
    recentDatapoints = json.loads(reasonData)["recentDatapoints"] if reasonData else [] 
    if recentDatapoints:
        eventOut['alarmValue'] = recentDatapoints[0]
    return eventOut

if __name__ == '__main__':
    test = {
  "version": "0",
  "id": "f4002e99-3d9c-4557-e244-ebbd7e78714d",
  "detail-type": "CloudWatch Alarm State Change",
  "source": "aws.cloudwatch",
  "account": "597377428377",
  "time": "2022-01-26T13:29:29Z",
  "region": "us-east-2",
  "resources": [
    "arn:aws:cloudwatch:us-east-2:597377428377:alarm:EC2-i-0455ae5e4ec01897c-High-Memory-Alarm"
  ],
  "detail": {
    "alarmName": "EC2-i-0455ae5e4ec01897c-High-Memory-Alarm",
    "state": {
      "value": "OK",
      "reason": "Threshold Crossed: 3 out of the last 3 datapoints [38.395433048854194 (26/01/22 13:24:00), 38.391752618786896 (26/01/22 13:19:00), 38.364239895660816 (26/01/22 13:14:00)] were not greater than or equal to the threshold (80.0) (minimum 1 datapoint for ALARM -> OK transition).",
      "reasonData": "{\"version\":\"1.0\",\"queryDate\":\"2022-01-26T13:29:29.292+0000\",\"startDate\":\"2022-01-26T13:14:00.000+0000\",\"statistic\":\"Average\",\"period\":300,\"recentDatapoints\":[38.364239895660816,38.391752618786896,38.395433048854194],\"threshold\":80.0,\"evaluatedDatapoints\":[{\"timestamp\":\"2022-01-26T13:24:00.000+0000\",\"sampleCount\":4.0,\"value\":38.395433048854194}]}",
      "timestamp": "2022-01-26T13:29:29.295+0000"
    },
    "previousState": {
      "value": "INSUFFICIENT_DATA",
      "reason": "Unchecked: Initial alarm creation",
      "timestamp": "2022-01-24T14:41:33.782+0000"
    },
    "configuration": {
      "metrics": [
        {
          "id": "52bf4b49-0fbd-8a08-fa8b-8f8cd8d5b92c",
          "metricStat": {
            "metric": {
              "namespace": "CWAgent",
              "name": "mem_used_percent",
              "dimensions": {
                "ImageId": "ami-0576aabae1709e005",
                "InstanceType": "t3.medium",
                "InstanceId": "i-0455ae5e4ec01897c",
                "AutoScalingGroupName": "eks-14bc213e-3074-758e-acf8-3d30e0637e72"
              }
            },
            "period": 300,
            "stat": "Average"
          },
          "returnData": True 
        }
      ]
    }
  }
}
    print(lambda_handler(test, None))
