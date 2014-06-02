#!/usr/bin/env python
'''
Validation Matrix: Platform - PCI DSS Audit module.

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
o = Evidence('2.2.2', 'netstat')
o.gather('/bin/netstat -plutn')

o.store()

# AV

o = Evidence('5.2', 'AV Settings')
o.gather('if [ -r /usr/local/etc/clamd.conf ]; then cat /usr/local/etc/clamd.conf; fi')
o.gather('cat /etc/cron.daily/viruscan.sh')
# latest scan log
o.gather('find /var/log/clamav/ -type f -iname scan-\* | sort | tail -n1 | xargs cat')
# time when virus scan runs
o.gather('cat /etc/anacrontab | grep "cron.daily"')


o.store()
#
# Patch Level
#

o = Evidence('6.1a', 'Patch level')
o.gather('cat /etc/redhat-release')
o.gather('for srv in httpd mod_security rsyslog ntp openldap-servers iptables openvas nmap postfix; do rpm -q $srv; done')
o.gather('rpm -qa | egrep "^jdk-.*"')
o.gather('if [ -x /var/ossec/bin/ossec-agentd ]; then /var/ossec/bin/ossec-agentd -V 2>&1 | head -n2 | tail -n1; fi')
o.gather('if [ -r /etc/snort/snort.conf ]; then snort -V 2>&1 ; fi')
o.gather('if [ -r /etc/openvpn/server.conf ]; then openvpn --version | head -n1; fi')
o.gather('if [ -x /usr/local/glassfish/glassfish/bin/asadmin ]; then /usr/local/glassfish/glassfish/bin/asadmin version  | egrep "^Version ="; fi')
# ClamAV Versions
o.gather('/usr/local/sbin/clamd --version')
# AV virus engine version
o.gather('cat /var/log/clamav/freshclam.log  | egrep \'(version:.*)\' | tail -n 40')

o.store()
#
# Access list 
#

o = Evidence('8.1', 'Access List')
o.gather('getent passwd')
o.gather('getent shadow')
o.gather('l=`ps auwwwx | egrep "\/usr\/sbin\/slapd" | wc -l`; if [ $l -ne 0 ]; then slapcat ; fi')

o.store()
#
# Password file
#

o = Evidence('8.4a', 'Password file')
o.gather('ls -lah /etc/shadow')

o.store()
#
# Password settings
#

o = Evidence('8.5.3,8.5.9,8.5.14', 'Password settings')
o.gather('/usr/bin/ldapsearch -x -b "cn=default,ou=pwpolicies,dc=fareoffice,dc=com"  -D cn=sssd,dc=fareoffice,dc=com -w \'dfj!!31DFq34lkdGE!gasoBXT34Dac\'')


o.store()
#
# Session Timeout Settings
#

o = Evidence('8.5.15', 'Session Timeout Settings')
o.gather('cat /etc/ssh/sshd_config | grep ClientAliveInterval')
o.gather('cat /etc/profile | grep TMOUT')

o.store()

# 
# Log Samples - Admin Actions
#
o = Evidence('5.2d, 10.2.2, 10.2.7', 'Log Samples - Admin Actions')
# find users that have logged in	
o.gather('cat /var/log/secure | egrep "pam_unix" | egrep "session opened for user" | tail -n 50')
o.gather('cat /var/log/secure | egrep "sudo" | tail -n 50')
o.gather('if [ -d /var/log/rsyslog/`date +%Y`/`date +%m`/`date +%d` ]; then cat /var/log/rsyslog/`date +%Y`/`date +%m`/`date +%d`/* | egrep "pam_unix" | egrep "session opened for user" | tail -n 50; fi')
o.gather('if [ -d /var/log/rsyslog/`date +%Y`/`date +%m`/`date +%d` ]; then cat /var/log/rsyslog/`date +%Y`/`date +%m`/`date +%d`/* | egrep "sudo" | tail -n 50; fi')

o.store()

# 
# Log Samples - AV
#

o = Evidence('5.2d, 10.2.2, 10.2.7', 'Log Samples - AV')
# find most recent log sample for clamscans 
o.gather('find /var/log/clamav/ -type f -iname scan-\* | head -n1 | xargs cat')
# provide freshclam logs
o.gather('if [ -r /var/log/clamav/freshclam.log ]; then tail -n 50 /var/log/clamav/freshclam.log; fi')

o.store()

#
# Log Samples - FIM
#
o = Evidence('10.2.7', 'Log Samples - FIM')
o.gather('if [ -r /var/ossec/logs/alerts/alerts.log ]; then tail -n 100 /var/ossec/logs/alerts/alerts.log; fi')
o.gather('if [ -r /var/log/snort/alert ]; then tail -n 100 /var/log/snort/alert; fi')
o.store()

#
# NTP settings and version
#

o = Evidence('10.4.a', 'NTP settings and version')
o.gather('if [ -r /etc/ntp.conf ]; then cat /etc/ntp.conf; else echo "NTP config not found."; fi')
o.gather('rpm -q ntp')

o.store()
#
# Running services
#

o = Evidence('2.2.2a', 'Running services')
o.gather('/bin/ps auwwwx | egrep -v auditPCI')

o.store()
#
# FIM Settings
#

o = Evidence('11.5.a', 'FIM Settings')
o.gather('if [ -r /var/ossec/etc/ossec.conf ]; then cat /var/ossec/etc/ossec.conf; else echo "OSSEC config file not found."; fi')
o.gather('if [ -r /etc/snort/snort.conf ]; then cat /etc/snort/snort.conf; else echo "SNORT config file not found."; fi')
o.gather('/sbin/iptables -L')

o.store()

#
# 2-Factor Authentication
#
o = Evidence('8.3', '2-Factor Authentication')
o.gather('if [ -r /etc/openvpn/server.conf ]; then cat /etc/openvpn/server.conf; fi')

o.store()

