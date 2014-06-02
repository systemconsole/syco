#!/usr/bin/env python
'''
Validation Matrix: Netowrk Devices - PCI DSS Audit module.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from evidence import Evidence


#
# Netstat
#
o = Evidence('2.2.3', 'netstat')
o.exclude('DATE.*')
o.exclude('XXX.*')
o.gather('netstat -an | grep LISTEN')

o.clear()
o.exclude('DATE.*')
o.exclude('XXX.*')
o.gather('netstat -an | grep ESTABLISHED')

o.store()


#
# Patch Level
#
