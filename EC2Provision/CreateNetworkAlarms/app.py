import os
import json
import boto3

def lambda_handler(event, context):
    print(f'Input: {event}')
    client = boto3.client('cloudwatch', region_name='us-east-2')
    metrics = [{
                'Id': 'ethtool_exceeded_packets',
                'Expression': 'RATE(SUM(METRICS()))*300',
                'Label': 'ethtool_exceeded_packets',
                'ReturnData': True
            }]
  
    for i in range(event['EniCount']):
        interface_id = f'eth{i}'
        metrics += [{
                'Id': f'ethtool_bw_out_allowance_exceeded_{i}',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'CWAgent',
                        'MetricName': 'ethtool_bw_out_allowance_exceeded',
                        'Dimensions': [{
                            'Name': 'AutoScalingGroupName',
                            'Value': event['AutoScalingGroupName']
                        },{
                            'Name': 'InstanceId',
                            'Value': event['InstanceId']
                        },{
                            'Name': 'ImageId',
                            'Value': event['ImageId']
                        },{
                            'Name': 'InstanceType',
                            'Value': event['InstanceType']
                        },{
                            'Name': 'driver',
                            'Value': 'ena'
                        },{
                            'Name': 'interface',
                            'Value': interface_id
                        }]
                    },
                    'Period': 300,
                    'Stat': 'Maximum'
                },
                'Label': f'ethtool_bw_out_allowance_exceeded_{i}',
                'ReturnData': False
            },{
                'Id': f'ethtool_conntrack_allowance_exceeded_{i}',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'CWAgent',
                        'MetricName': 'ethtool_conntrack_allowance_exceeded',
                        'Dimensions': [{
                            'Name': 'AutoScalingGroupName',
                            'Value': event['AutoScalingGroupName']
                        },{
                            'Name': 'InstanceId',
                            'Value': event['InstanceId']
                        },{
                            'Name': 'ImageId',
                            'Value': event['ImageId']
                        },{
                            'Name': 'InstanceType',
                            'Value': event['InstanceType']
                        },{
                            'Name': 'driver',
                            'Value': 'ena'
                        },{
                            'Name': 'interface',
                            'Value': interface_id
                        }]
                    },
                    'Period': 300,
                    'Stat': 'Maximum'
                },
                'Label': f'ethtool_conntrack_allowance_exceeded_{i}',
                'ReturnData': False
            },{
                'Id': f'ethtool_linklocal_allowance_exceeded_{i}',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'CWAgent',
                        'MetricName': 'ethtool_linklocal_allowance_exceeded',
                        'Dimensions': [{
                            'Name': 'AutoScalingGroupName',
                            'Value': event['AutoScalingGroupName']
                        },{
                            'Name': 'InstanceId',
                            'Value': event['InstanceId']
                        },{
                            'Name': 'ImageId',
                            'Value': event['ImageId']
                        },{
                            'Name': 'InstanceType',
                            'Value': event['InstanceType']
                        },{
                            'Name': 'driver',
                            'Value': 'ena'
                        },{
                            'Name': 'interface',
                            'Value': interface_id
                        }]
                    },
                    'Period': 300,
                    'Stat': 'Maximum'
                },
                'Label': f'ethtool_linklocal_allowance_exceeded_{i}',
                'ReturnData': False
            },{
                'Id': f'ethtool_bw_in_allowance_exceeded_{i}',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'CWAgent',
                        'MetricName': 'ethtool_bw_in_allowance_exceeded',
                        'Dimensions': [{
                            'Name': 'AutoScalingGroupName',
                            'Value': event['AutoScalingGroupName']
                        },{
                            'Name': 'InstanceId',
                            'Value': event['InstanceId']
                        },{
                            'Name': 'ImageId',
                            'Value': event['ImageId']
                        },{
                            'Name': 'InstanceType',
                            'Value': event['InstanceType']
                        },{
                            'Name': 'driver',
                            'Value': 'ena'
                        },{
                            'Name': 'interface',
                            'Value': interface_id
                        }]
                    },
                    'Period': 300,
                    'Stat': 'Maximum'
                },
                'Label': f'ethtool_bw_in_allowance_exceeded_{i}',
                'ReturnData': False
            },{
                'Id': f'ethtool_pps_allowance_exceeded_{i}',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'CWAgent',
                        'MetricName': 'ethtool_pps_allowance_exceeded',
                        'Dimensions': [{
                            'Name': 'AutoScalingGroupName',
                            'Value': event['AutoScalingGroupName']
                        },{
                            'Name': 'InstanceId',
                            'Value': event['InstanceId']
                        },{
                            'Name': 'ImageId',
                            'Value': event['ImageId']
                        },{
                            'Name': 'InstanceType',
                            'Value': event['InstanceType']
                        },{
                            'Name': 'driver',
                            'Value': 'ena' 
                        },{
                            'Name': 'interface',
                            'Value': interface_id 
                        }]
                    },
                    'Period': 300,
                    'Stat': 'Maximum'
                },
                'Label': f'ethtool_pps_allowance_exceeded_{i}',
                'ReturnData': False
            }]
    response = client.put_metric_alarm(
        AlarmName=f'EC2-{event["InstanceId"]}-High-ExceededPackets-Alarm',
        ActionsEnabled=False,
        Metrics=metrics,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=int(os.getenv('EXCEEDED_BYTES_THRESHOLD', '80')),
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    return event

if __name__ == '__main__':
    test = {
      "account": "597377428377",
      "region": "us-east-2",
      "timestamp": "2022-01-25T17:26:24+0800",
      "time": "17:26:24",
      "InstanceId": "i-0455ae5e4ec01897c",
      "State": "running",
      "ImageId": "ami-0530e887f0618aec0",
      "InstanceType": "t3.medium",
      "InstanceName": "ecs-node",
      "AutoScalingGroupName": "eks-14bc213e-3074-758e-acf8-3d30e0637e72",
      "PrivateIpAddress": "10.0.0.106"
    } 
    lambda_handler(test, None)

