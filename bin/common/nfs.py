#!/usr/bin/env python
'''
Functions to handle NFS exports.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import app
import general
import iptables
from iptables import iptables

def add_export(path):
  general.set_config_property("/etc/exports", "^" + path + ".*$", path + " *(rw)")

def remove_export(path):
  general.set_config_property("/etc/exports", "")

def restart_services():
  general.shell_exec("service portmap restart")
  general.shell_exec("service nfs restart")
  general.shell_exec("service rpcsvcgssd restart")

def stop_services():
  general.shell_exec("service nfs stop")
  general.shell_exec("service portmap stop")

def configure_with_static_ip():
  '''
  http://www.cyberciti.biz/faq/centos-fedora-rhel-iptables-open-nfs-server-ports/

  '''
  app.print_verbose("Configure nfs static server ports.")
  # TCP port rpc.lockd should listen on.
  general.set_config_property("/etc/sysconfig/nfs", ".*LOCKD_TCPPORT.*", "LOCKD_TCPPORT=32803")

  # UDP port rpc.lockd should listen on.
  general.set_config_property("/etc/sysconfig/nfs", ".*LOCKD_UDPPORT.*", "LOCKD_UDPPORT=32769")

  # Port rpc.mountd should listen on.
  general.set_config_property("/etc/sysconfig/nfs", ".*MOUNTD_PORT.*", "MOUNTD_PORT=892")

  # Port rquotad should listen on.
  general.set_config_property("/etc/sysconfig/nfs", ".*RQUOTAD_PORT.*", "RQUOTAD_PORT=875")

  # Port rpc.statd should listen on.
  general.set_config_property("/etc/sysconfig/nfs", ".*STATD_PORT.*", "STATD_PORT=662")

  # Outgoing port statd should used. The default is port is random
  general.set_config_property("/etc/sysconfig/nfs", ".*STATD_OUTGOING_PORT.*", "STATD_OUTGOING_PORT=2020")

def add_iptables_rules():
  '''
  Open iptables for NFS just during the installation.

  '''
  app.print_verbose("Setup iptables for nfs")
  remove_iptables_rules()

  iptables("-N nfs_export")
  iptables("-A nfs_export -m state --state NEW -p tcp --dport 32803 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p tcp --dport 32769 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p tcp --dport 892 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p tcp --dport 875 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p tcp --dport 662 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p tcp --dport 2020 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p tcp --dport 2049 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p tcp --dport 111 -j ACCEPT")

  iptables("-A nfs_export -m state --state NEW -p udp --dport 32803 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p udp --dport 32769 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p udp --dport 892 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p udp --dport 875 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p udp --dport 662 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p udp --dport 2020 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p udp --dport 2049 -j ACCEPT")
  iptables("-A nfs_export -m state --state NEW -p udp --dport 111 -j ACCEPT")

  iptables("-I INPUT  -p ALL -j nfs_export")
  iptables("-I OUTPUT -p ALL -j nfs_export")

def remove_iptables_rules():
  iptables("-D INPUT  -p ALL -j nfs_export")
  iptables("-D OUTPUT -p ALL -j nfs_export")
  iptables("-F nfs_export")
  iptables("-X nfs_export")