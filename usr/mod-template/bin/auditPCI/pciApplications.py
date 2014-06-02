#!/usr/bin/env python
'''
Validation Matrix: Application - PCI DSS Audit module.

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
# Transaction Logs
#

o = Evidence('3.4b', 'Transaction Logs')
# gather transaction logs
o.gather('if [ -d /var/log/farepayment/ ]; then find /var/log/farepayment/ -type f -iname \*.log | head -n1; fi')

o.store()


#
# Valid SSL Certificates
#

o = Evidence('4.1b', 'Valid SSL Certificates')
# 
o.gather('cert=`mktemp`; /usr/bin/openssl s_client -connect 10.101.1.125:443 2>/dev/null >$cert && openssl x509 -in $cert -text && rm -f $cert')
o.gather('cert=`mktemp`; /usr/bin/openssl s_client -connect 10.101.2.125:443 2>/dev/null >$cert && openssl x509 -in $cert -text && rm -f $cert')

o.store()

#
# Patch Level Applications (maybe by hand, ask developer)
#

#o.gather(

#
# Application Access List 
#

# ask Johann

#
# Service Protocol Listing
#

# ask Johann


#
# Password Settings
#

# ask Johann

#
# Session Timeout Settings
#

# ask developer

#
# Log Samples - Admin Actions
#

o = Evidence('10.2.2', 'Application Log Samples - Admin Actions')
# gather log samples - admin actions
o.gather('if [ -r /usr/local/glassfish/glassfish/domains/domain1/logs/server.log ]; then cat /usr/local/glassfish/glassfish/domains/domain1/logs/server.log | grep "logged in with group access to [[superadminusers]]"; fi')

o.store()


