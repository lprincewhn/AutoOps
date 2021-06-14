import os
import boto3

def lambda_handler(event, context):
    print(f'Event In: {event}')
    client = ec2 = boto3.client('cloudwatch')
    ary = event["domainId"].split('/')
    clientId = ary[0]
    domainName = ary[1]
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-ClusterStatus.red-Alarm',
        ActionsEnabled=False,
        MetricName='ClusterStatus.red',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-ClusterStatus.yellow-Alarm',
        ActionsEnabled=False,
        MetricName='ClusterStatus.yellow',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')    
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-Low-FreeStorageSpace-Alarm',
        ActionsEnabled=False,
        MetricName='FreeStorageSpace',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=int(os.getenv('FreeStorageSpace_Threshold', '20480')),
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}')
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-ClusterIndexWritesBlocked-Alarm',
        ActionsEnabled=False,
        MetricName='ClusterIndexWritesBlocked',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-Low-Nodes-Alarm',
        ActionsEnabled=False,
        MetricName='Nodes',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=86400,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=int(os.getenv('Nodes_Threshold', '1')),
        ComparisonOperator='LessThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-AutomatedSnapshotFailure-Alarm',
        ActionsEnabled=False,
        MetricName='AutomatedSnapshotFailure',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-High-CPUUtilization-Alarm',
        ActionsEnabled=False,
        MetricName='CPUUtilization',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=300,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=80,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-High-WarmCPUUtilization-Alarm',
        ActionsEnabled=False,
        MetricName='WarmCPUUtilization',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=300,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=80,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-High-JVMMemoryPressure-Alarm',
        ActionsEnabled=False,
        MetricName='JVMMemoryPressure',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=300,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=80,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-High-WarmJVMMemoryPressure-Alarm',
        ActionsEnabled=False,
        MetricName='WarmJVMMemoryPressure',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=300,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=80,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-High-MasterCPUUtilization-Alarm',
        ActionsEnabled=False,
        MetricName='MasterCPUUtilization',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=300,
        EvaluationPeriods=3,
        DatapointsToAlarm=3,
        Threshold=50,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-High-MasterJVMMemoryPressure-Alarm',
        ActionsEnabled=False,
        MetricName='MasterJVMMemoryPressure',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=300,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=50,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-KMSKeyError-Alarm',
        ActionsEnabled=False,
        MetricName='KMSKeyError',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    response = client.put_metric_alarm(
        AlarmName=f'ElasticSearch-{domainName}-KMSKeyInaccessible-Alarm',
        ActionsEnabled=False,
        MetricName='KMSKeyInaccessible',
        Namespace='AWS/ES',
        Statistic='Average',
        Dimensions=[{
            'Name': 'ClientId',
            'Value': clientId
        },{
            'Name': 'DomainName',
            'Value': domainName
        }],
        Period=60,
        EvaluationPeriods=1,
        DatapointsToAlarm=1,
        Threshold=1,
        ComparisonOperator='GreaterThanOrEqualToThreshold',
        TreatMissingData='missing',
        Tags=[]
    )
    print(f'Response: {response}') 
    return event
