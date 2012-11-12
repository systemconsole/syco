#!/usr/bin/python

import os
import commands

status = "OK"

output = commands.getstatusoutput("/usr/lib64/nagios/plugins/check_disk -w 10% -c 5% -p /dev/mapper/VolGroup00-lv_root " + \
    "-p /dev/mapper/VolGroup00-lv_home " \
    "-p  dev/mapper/VolGroup00-lv_tmp " \
    "-p /dev/mapper/VolGroup00-lv_log " \
    "-p /dev/mapper/VolGroup00-lv_vartmp " \
    "-p /dev/mapper/VolGroup00-lv_swap")
 
print output


#/dev/mapper/VolGroup00-lv_root 
#/dev/mapper/VolGroup00-lv_home 
#/dev/mapper/VolGroup00-lv_tmp 
#/dev/mapper/VolGroup00-lv_log 
#/dev/mapper/VolGroup00-lv_vartmp 
#/dev/mapper/VolGroup00-lv_swap  
