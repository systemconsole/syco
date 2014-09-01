#!/usr/bin/env python
'''
A simple check to check the ulimit setting for a specific user and send an alarm to Icinga
if the open files is getting close to the allowed limit on the system

Will be seen as a module for Icinga with ok, warn and critical settings.

Author: David Skeppstedt
Version: 0.000.0.0.1 Beta

Filename: 
  /usr/lib64/nagios/plugins/check_ulimit.py

Manual commands: (To be sycofied together with glassfish installation)
  chmod 755 /usr/lib64/nagios/plugins/check_ulimit.py
  chown nrpe:nrpe /usr/lib64/nagios/plugins/check_ulimit.py
  chcon -t nagios_unconfined_plugin_exec_t /usr/lib64/nagios/plugins/check_ulimit.py
  semanage fcontext -a -t nagios_unconfined_plugin_exec_t /usr/lib64/nagios/plugins/check_ulimit.py
  echo "nrpe ALL=NOPASSWD:/usr/lib64/nagios/plugins/check_ulimit.py" >> /etc/sudoers.d/nrpe
  echo "command[check_ulimit_glassfish]=/usr/lib64/nagios/plugins/check_ulimit.py glassfish 60 80" >> /etc/nagios/nrpe.d/common.cfg
  echo "nrpe ALL=(glassfish) NOPASSWD: /bin/cat" >> /etc/sudoers.d/nrpe
  service nrpe restart

The manual commands will be sycofied togheter with the glassfish installation and will be default monitoring for glashfish suite.

'''

import os
import subprocess
import sys

if len(sys.argv) != 4:
    sys.exit('Usage: {0} [username] [warn_percent] [crit_percent] :: Example: {0} glassfish 60 80'.format(sys.argv[0],sys.argv[0]))

username = sys.argv[1]
warn = int(sys.argv[2])
crit = int(sys.argv[3])

limit =  int(subprocess.Popen("sudo -u glassfish cat /proc/self/limits | grep 'open files' | awk '{ print $4 }'", shell=True, stdout=subprocess.PIPE).stdout.read().strip())
current = int(subprocess.Popen("sudo lsof | grep ' glassfish ' | awk '{print $NF}' | sort | wc -l", shell=True, stdout=subprocess.PIPE).stdout.read().strip())

percent =  int(round(((float(current) / float(limit)) * 100),0))

if percent >= warn:
    if percent >= crit:
        print("ULIMIT CRITICAL: Openfiles for {0} is {1} ({2}%) of {3} allowed | 'Openfiles'={1}".format(username,current,percent,limit))
        sys.exit(2)
    else:
        print("ULIMIT WARNING: Openfiles for {0} is {1} ({2}%) of {3} allowed | 'Openfiles'={1}".format(username,current,percent,limit))
        sys.exit(1)
else:
    print("ULIMIT OK: Openfiles for {0} is {1} ({2}%) of {3} allowed; | 'Openfiles'={1}".format(username,current,percent,limit))
    sys.exit(0)
