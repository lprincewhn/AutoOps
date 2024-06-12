import string
import datetime

def lambda_handler(event, context):
    print(f'Input: {event}')
    alarmName = event.get('detail').get('alarmName')
    state = event.get('detail').get('state').get('value')
    volume_details = None
    if alarmName.startswith('DiskSpace') and state == 'ALARM':
        metrics = event.get('detail').get('configuration').get('metrics')
        metricName = metrics[0].get('metricStat').get('metric').get('name')
        dimensions = metrics[0].get('metricStat').get('metric').get('dimensions')
        device = dimensions.get('device')
        volume_details = {
            'InstanceId': dimensions.get('InstanceId'),
            'metricName': metricName,
            'path': dimensions.get('path'),
            'device': device,
            'fstype': dimensions.get('fstype'),
            'DeviceName': '/dev/' + device.rstrip(string.digits) if device else None,
            'PartitionNum': device[-(len(device)-len(device.rstrip(string.digits))):] if device else None,
            'MountPoint': dimensions.get('path'),
            'DriveLetter': dimensions.get('instance')[0] if dimensions.get('instance') else None
        }
        return volume_details
    raise Exception('Event not supported')
