#!/usr/bin/env python
'''
A simple file to check and monitor the temperature of the USB Temperature Reader.

Will be seen as a module for Icinga with warn and critical settings.

Author: David Skeppstedt
Version: 0.000.0.0.1 Beta

'''

import os
import subprocess
import sys

if len(sys.argv) < 2:
    sys.exit('Usage: {0} [warnlevel] [critlevel] :: Example: {0} 20 25'.format(sys.argv[0],sys.argv[0]))

extapp = subprocess.Popen(["/usr/bin/checktemp","-c"], stdout=subprocess.PIPE)
temp = extapp.communicate()[0]

if temp >= sys.argv[1]:
    if temp >= sys.argv[2]:
        print("TEMP CRITICAL: Temperature is {0}c | 'Temp'={0}".format(temp.strip()))
        sys.exit(2)
    else:
        print("TEMP WARNING: Temperature is {0}c | 'Temp'={0}".format(temp.strip()))
        sys.exit(1)
else:
    print("TEMP OK: Temperature is {0}c | 'Temp'={0}".format(temp.strip()))
     sys.exit(0)
