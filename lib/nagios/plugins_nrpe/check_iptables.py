#!/usr/bin/env python
'''
NRPE check for number of iptables rules.

'''

__author__ = "Elis Kullberg <elis.kullberg@netlight.se>"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import commands
import sys

filename = "/tmp/syco-firewall-line-count"

[status, newLineCount] = commands.getstatusoutput("/sbin/iptables -L | wc -l")
[catstatus, oldLineCount] = commands.getstatusoutput("cat {0}".format(filename))

def w(string):
    f = open(filename, "w")
    f.write(string)
    f.close()

# Probably the first time the script is executed.
if catstatus != 0:
    w(newLineCount)
    print "I/O Issue"
    sys.exit(3)

# Probably not allowed to execute iptables.
elif status != 0:
    print "Permissions problem"
    sys.exit(3)

# No changes since last check.
elif newLineCount == oldLineCount:
    w(newLineCount)
    print "OK"
    sys.exit(0)

# Something has changed since last check.
else:
    print "CRITICAL: {0} needs to be removed.".format(filename)
    sys.exit(2)
