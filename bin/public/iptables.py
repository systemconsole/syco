#!/usr/bin/env python
'''
Setup an iptable firewall according to the installed services.

If for example mysql installed, port 3306 will be opened for incoming.

This script is based on Oskar Andreassons rc.DMZ.firewall.txt
Read and learn more about iptables.
http://www.frozentux.net/iptables-tutorial/scripts/rc.DMZ.firewall.txt
http://www.frozentux.net/iptables-tutorial/iptables-tutorial.html
http://manpages.ubuntu.com/manpages/jaunty/man8/iptables.8.html
http://www.cipherdyne.org/psad/

TODO:
* Add recent http://www.snowman.net/projects/ipt_recent/
  http://www.frozentux.net/iptables-tutorial/scripts/recent-match.txt
* SSH to the server should only be allowed from certain ips.

Changelog:
110211 DALI - Allow GPG to talk to keyserver.ubuntu.com:11371
110205 DALI - Added allowed_udp chain to use with UDP rules.
110205 DALI - Added support for httpd and modsecurity.
110129 DALI - Adding file header and comments
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel.lindh@cybercow.se"
__credits__ = ["Oskar Andreasson"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import app, general, net
from installGlassfish import GLASSFISH_PATH

def build_commands(commands):
  commands.add("iptables-clear", iptables_clear, help="Clear all rules from iptables.")
  commands.add("iptables-setup", iptables_setup, help="Setup an iptable firewall, customized for installed services.")

def iptables_clear(args):
  '''
  Remove all iptables rules.

  '''
  app.print_verbose("Clear all iptables rules.")
  # reset the default policies in the filter table.
  iptables("-P INPUT ACCEPT")
  iptables("-P FORWARD ACCEPT")
  iptables("-P OUTPUT ACCEPT")

  # reset the default policies in the nat table.
  iptables("-t nat -P PREROUTING ACCEPT")
  iptables("-t nat -P POSTROUTING ACCEPT")
  iptables("-t nat -P OUTPUT ACCEPT")

  # reset the default policies in the mangle table.
  iptables("-t mangle -P PREROUTING ACCEPT")
  iptables("-t mangle -P POSTROUTING ACCEPT")
  iptables("-t mangle -P INPUT ACCEPT")
  iptables("-t mangle -P OUTPUT ACCEPT")
  iptables("-t mangle -P FORWARD ACCEPT")

  # Flush all chains
  iptables("-F -t filter")
  iptables("-F -t nat")
  iptables("-F -t mangle")

  # Delete all user-defined chains
  iptables("-X -t filter")
  iptables("-X -t nat")
  iptables("-X -t mangle")

  # Zero all counters
  iptables("-Z -t filter")
  iptables("-Z -t nat")
  iptables("-Z -t mangle")

def iptables_setup(args):
  iptables_clear(args)
  _deny_all()
  _create_chains()
  _setup_general_rules()
  _setup_ssh_rules()
  _setup_dns_resolver_rules()
  _setup_gpg_rules()
  _setup_installation_server_rules()

  if (os.access("/etc/ntp", os.F_OK)):
    _setup_ntp_rules()

  if (os.access("/usr/bin/mysqld_safe", os.F_OK)):
    _setup_mysql_rules()

  if (os.access(GLASSFISH_PATH, os.F_OK)):
    _setup_glassfish_rules()

  if (os.path.exists('/etc/httpd/conf/httpd.conf')):
    _setup_httpd()

  _closing_chains()
  _setup_postrouting()
  _iptables_save()

def iptables(args):
  general.shell_exec("/sbin/iptables " + args)

#
# Private members
#

def _deny_all():
  app.print_verbose("Deny all.")
  iptables("-P INPUT DROP")
  iptables("-P FORWARD DROP")
  iptables("-P OUTPUT DROP")

def _create_chains():
  app.print_verbose("Create bad_tcp_packets chain.")
  iptables("-N bad_tcp_packets")
  iptables("-A bad_tcp_packets -p tcp --tcp-flags SYN,ACK SYN,ACK -m state --state NEW -j REJECT --reject-with tcp-reset")
  iptables("-A bad_tcp_packets -p tcp ! --syn -m state --state NEW -j LOG --log-prefix 'IPT: New not syn:'")
  iptables("-A bad_tcp_packets -p tcp ! --syn -m state --state NEW -j DROP")

  app.print_verbose("Create allowed chain.")
  iptables("-N allowed")
  iptables("-A allowed -p TCP --syn -j ACCEPT")
  iptables("-A allowed -p TCP -m state --state ESTABLISHED,RELATED -j ACCEPT")
  iptables("-A allowed -p TCP -j DROP")

  app.print_verbose("Create allowed chain.")
  iptables("-N allowed_udp")
  iptables("-A allowed_udp -p UDP -j ACCEPT")
  # TODO: Possible to restrict more?
  #iptables("-A allowed_udp -p UDP --syn -j ACCEPT")
  #iptables("-A allowed_udp -p UDP -m state --state ESTABLISHED,RELATED -j ACCEPT")
  #iptables("-A allowed_udp -p UDP -j DROP")

  app.print_verbose("Create ICMP rules.")
  iptables("-N icmp_packets")
  iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type echo-request -j ACCEPT")
  iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type echo-reply -j ACCEPT")
  iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type destination-unreachable -j ACCEPT")
  iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type source-quench -j ACCEPT")
  iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type time-exceeded -j ACCEPT")
  iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type parameter-problem -j ACCEPT")

def _setup_general_rules():
  app.print_verbose("Bad TCP packets we don't want.")
  iptables("-A INPUT   -p tcp -j bad_tcp_packets")
  iptables("-A OUTPUT  -p tcp -j bad_tcp_packets")
  iptables("-A FORWARD -p tcp -j bad_tcp_packets")

  app.print_verbose("Standard icmp_packets from anywhere.")
  iptables("-A INPUT  -p ICMP -j icmp_packets")
  iptables("-A OUTPUT -p ICMP -j icmp_packets")

  app.print_verbose("From Localhost interface to Localhost IP's.")
  iptables("-A INPUT -p ALL -i lo -s 127.0.0.1 -j ACCEPT")
  iptables("-A OUTPUT -p ALL -o lo -d 127.0.0.1 -j ACCEPT")

def _setup_ssh_rules():
  '''
  Can SSH to this and any other computer internal and external.

  '''
  app.print_verbose("Setup ssh INPUT/OUTPUT rule.")
  ssh_ports="22,34"
  iptables("-A INPUT -p tcp  -m multiport --dports " + ssh_ports + " -j allowed")
  iptables("-A OUTPUT -p tcp -m multiport --dports " + ssh_ports + " -j ACCEPT")

def _setup_dns_resolver_rules():
  '''
  Allow this server to communicate with an dns resolver.

  '''
  inet_ip=net.get_lan_ip()
  for resolver_ip in app.get_dns_resolvers().split(" "):
    iptables("-A OUTPUT -p udp -s " + inet_ip + " --sport 1024:65535 -d " + resolver_ip + " --dport 53 -m state --state NEW,ESTABLISHED -j ACCEPT")
    iptables("-A INPUT  -p udp -s " + resolver_ip + " --sport 53 -d  " + inet_ip + "  --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT")
    iptables("-A OUTPUT -p tcp -s " + inet_ip + "  --sport 1024:65535 -d " + resolver_ip + " --dport 53 -m state --state NEW,ESTABLISHED -j ACCEPT")
    iptables("-A INPUT  -p tcp -s " + resolver_ip + " --sport 53 -d  " + inet_ip + "  --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT")

def _setup_gpg_rules():
  # Allow GPG to talk to keyserver.ubuntu.com:11371
  iptables("-A OUTPUT -p tcp -d 91.189.89.49 --dport 11371 -j allowed")

def _setup_installation_server_rules():
  '''
  Open http access to the installation server.

  TODO: Move all repos to the install server and harden the iptables.

  '''
  app.print_verbose("Setup http access to installation server.")
  #ip=app.get_installation_server_ip()
  #iptables("-A OUTPUT -p tcp -d " + ip + " -m multiport --dports 80,443 -j ACCEPT")
  iptables("-A OUTPUT -p tcp -m multiport --dports 80,443 -j ACCEPT")

def _setup_ntp_rules():
  '''
  Allow NTP client/server traffic.

  TODO: Only allow traffic to dedicated NTP servers and clients.
        Maybe this rule need to be in installNTP.py.

  '''
  app.print_verbose("Setup NTP input/output rule.")
  iptables("-A INPUT  -p UDP --dport 123 -j allowed_udp")
  iptables("-A OUTPUT -p UDP --dport 123 -j allowed_udp")

def _setup_mysql_rules():
  app.print_verbose("Setup mysql input rule.")
  iptables("-A INPUT -p TCP -m multiport --dports 3306 -j allowed")

  iptables("-A OUTPUT -p TCP -m multiport -d " + app.get_mysql_primary_master()   + " --dports 3306 -j allowed")
  iptables("-A OUTPUT -p TCP -m multiport -d " + app.get_mysql_secondary_master() + " --dports 3306 -j allowed")

def _setup_glassfish_rules():
  app.print_verbose("Setup glassfish input rule.")
  glassfish_ports="6048,6080,6081,7048,7080,7081"
  iptables("-A INPUT -p TCP -m multiport --dports " + glassfish_ports + " -j allowed")

  iptables("-A OUTPUT -p TCP -m multiport -d " + app.get_mysql_primary_master()   + " --dports 3306 -j allowed")
  iptables("-A OUTPUT -p TCP -m multiport -d " + app.get_mysql_secondary_master() + " --dports 3306 -j allowed")

def _setup_httpd():
  app.print_verbose("Setup httpd input rule.")
  iptables("-A INPUT -p TCP -m multiport --dports 80,443 -j allowed")

def _closing_chains():
  app.print_verbose("Allow all established and related packets incoming from anywhere.")
  iptables("-A INPUT -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT")
  iptables("-A OUTPUT -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT")
  iptables("-A FORWARD -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT")

  app.print_verbose("Log weird packets that don't match the above.")
  iptables("-A INPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix 'IPT: INPUT packet died: '")
  iptables("-A OUTPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix 'IPT: OUTPUT packet died: '")
  iptables("-A FORWARD -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix 'IPT: FORWARD packet died: '")

def _setup_postrouting():
  app.print_verbose("Enable simple IP Forwarding and Network Address Translation.")
  #iptables("-t nat -A POSTROUTING -o $INET_IFACE -j SNAT --to-source $inet_ip")
  #iptables("-t nat -A POSTROUTING -o eth0 -j MASQUERADE")

def _iptables_save():
  app.print_verbose("Save current iptables rules to /etc/iptables.")
  general.shell_exec("/sbin/iptables-save > /etc/sysconfig/iptables")
