#!/usr/bin/python
import commands
import sys

[status,newLineCount] = commands.getstatusoutput("/sbin/iptables -L | wc -l")
[catstatus,oldLineCount] = commands.getstatusoutput("cat /tmp/firewalllinecount")

def w(string):
    f = open("/tmp/firewalllinecount", "w")
    f.write(string)
    f.close()

if catstatus != 0:
    w(newLineCount)
    print "I/O Issue"
    sys.exit(3)
elif status != 0:
    w(newLineCount)
    print "Permissions problem"
    sys.exit(3)
elif newLineCount == oldLineCount:
    w(newLineCount)
    print "OK"
    sys.exit(0)
else:
    w(newLineCount)
    print "CRITICAL"
    sys.exit(2)


