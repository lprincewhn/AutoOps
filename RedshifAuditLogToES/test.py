content='''
1|rdsdb | |alter |1|1|1|9223372036854775807|29387|1076|Tue, 22 Jun 2021 15:13:25:978
100|awsuser | |create |1|1|0|9223372036854775807|29415|1101|Tue, 22 Jun 2021 15:13:26:658
'''

items = content.split('\n')
for i in items:
    fields = i.split('|')
    if len(fields)>=11:
        record = {
                "userid": fields[0],
                "username": fields[1],
                "oldusername": fields[2],
                "action": fields[3],
                "usecreatedb": fields[4],  
                "usesuper": fields[5],
                "usecatupd": fields[6],
                "valuntil": fields[7],
                "pid": fields[8],
                "xid": fields[9],  
                "recordtime": fields[10]
        }
        print(record)
