#!/usr/bin/env python
'''
Validation Matrix: Iptables Firewall - PCI DSS Audit module.

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
# Nmap
#


o = Evidence('2.2.2a', 'Nmap')
# gather listening tcp ports via nmap for this datacenters firewall and the other datacenters firewall
o.gather('if [[ `hostname` =~ ^fw.*$ ]]; then /usr/bin/nmap -sT -O 10.101.1.1 2>&1; fi')
o.gather('if [[ `hostname` =~ ^fw.*$ ]]; then /usr/bin/nmap -sT -O 10.101.2.1 2>&1; fi')

o.store()

#
# Anti Spoofing
#

o = Evidence('1.3.8.a', 'Anti Spoofing')
# gather anti spoofing from netfilter
o.gather('if [ -r /proc/sys/net/ipv4/conf/br1/rp_filter ]; then if [ `cat /proc/sys/net/ipv4/conf/br1/rp_filter` -eq 1 ]; then echo "Antispoofing enabled."; else echo "Antispoofing disabled."; fi; fi')

o.store()


#
# Stateful Packet Inspection
#

o = Evidence('1.3.6', 'Stateful Packet Inspection')
# gather the stateful packet inspection
o.gather('/sbin/lsmod | grep nf_conntrack')
o.gather('/sbin/iptables-save | egrep \'(-m state|--state)\'')

o.store()

