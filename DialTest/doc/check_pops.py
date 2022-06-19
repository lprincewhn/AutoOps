import os
import sys
import socket 
import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if os.getenv("DEBUG", None) else logging.INFO)

cf_domainname = sys.argv[1] 

fh = open('poplist.csv')
fout = open(cf_domainname+'.csv', 'w')
for line in fh.readlines()[1:]:
    popid = line.split(',')[0]
    popdomain = f'{cf_domainname.split(".")[0]}.{popid}.cloudfront.net'
    try:
        logger.debug(popdomain)
        popip = socket.gethostbyname(popdomain)
        print(popip)
        fout.write(f'{line.strip()},{popip}\n')
    except Exception as e:
        logger.warning(e)

