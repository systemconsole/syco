#!/usr/bin/python

import commands
import sys
import hashlib
import os

digest = hashlib.md5(commands.getstatusoutput("snmpwalk -v3 -u nagios -n '' -l AuthPriv -a SHA -x AES -c public -A fo5Loogo -X fo5Loogo -m all 10.100.2.220 dot1dTpFdbAddress")[1]).hexdigest()
[catstatus, olddigest] = commands.getstatusoutput("cat /tmp/switchmacs")

def w(string):
    f = open("/tmp/switchmacs", "w")
    f.write(string)
    f.close()

if (catstatus != 0 or (digest == olddigest and olddigest != "")):
    w(digest)
    print "OK"
    sys.exit(0)
else:
    w(digest)
    print "CRITICAL"
    sys.exit(2)





#print digest
