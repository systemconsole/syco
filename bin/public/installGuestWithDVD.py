#!/usr/bin/env python
'''
Install a KVM guest from DVD instead of cobbler, that most syco servers uses
for installation.

This script should be executed directly on a kvm host.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import time

import app
import general
import net
from iptables import iptables

def build_commands(commands):
  commands.add("install-guest", install_guest, "hostname, ip", help="Install kvm guest from dvd, without cobbler.")

# The main function
#
def install_guest(args):

  if (len(args) != 3):
    app.print_error("What server and ip should you use?")
    return

  hostname = args[1]
  ip = args[2]

  app.print_verbose("Instal kvm guest " + hostname + " with ip " + ip )
  
  # Is server already installed?
  result = general.shell_exec("virsh list --all")
  if (hostname in result):
    app.print_error(hostname + " already installed")
    return

  # Mount dvd
  if (not os.access("/media/dvd", os.F_OK)):
    general.shell_exec("mkdir /media/dvd")

  if (not os.path.ismount("/media/dvd")):
    general.shell_exec("mount -o ro /dev/dvd /media/dvd")

  # Create kickstart for the installation
  general.shell_exec("mkdir -p " + app.SYCO_PATH + "var/kickstart/generated")
  ks_path = app.SYCO_PATH + "var/kickstart/generated/" + hostname + ".ks"
  general.shell_exec("cp " + app.SYCO_PATH + "var/kickstart/dvd-guest.ks " + ks_path)
  general.set_config_property(ks_path, "\$\{HOSTNAME\}", hostname)
  general.set_config_property(ks_path, "\$\{IP\}", ip)
  general.set_config_property(ks_path, "\$\{GATEWAY\}", app.get_gateway_server_ip())
  general.set_config_property(ks_path, "\$\{NAMESERVER\}", app.get_first_dns_resolver())
  general.set_config_property(ks_path, "\$\{ROOT_PASSWORD\}", app.get_root_password_hash())

  # Export kickstart file
  general.set_config_property("/etc/exports", '^' + app.SYCO_PATH + 'var/kickstart/generated.*$', app.SYCO_PATH + "var/kickstart/generated *(rw)")
  general.set_config_property("/etc/exports", '^/media/dvd/.*$', "/media/dvd/ *(rw)")

  configure_nfs_with_static_ip()
  add_temporary_nfs_iptables_rules()
  restart_all_nfs_services()

  # Create the data lvm volumegroup
  result = general.shell_exec("lvdisplay -v /dev/VolGroup00/" + hostname)
  if ("/dev/VolGroup00/" + hostname not in result):
    general.shell_exec("lvcreate -n " + hostname + " -L 100G VolGroup00")

  # Create the KVM image
  local_ip = net.get_lan_ip()
  general.shell_exec("virt-install --connect qemu:///system --name " + hostname + " --ram 2048 --vcpus=2 " +
    "--disk path=/dev/VolGroup00/" + hostname + " " +
    "--location nfs:" + local_ip + ":/media/dvd " +
    "--vnc --noautoconsole --hvm --accelerate " +
    "--check-cpu " +
    "--os-type linux --os-variant=rhel5.4 " +
    "--network=bridge:br1 " +
    '-x "ks=nfs:' + local_ip + ':' + ks_path + '"')

  # Waiting for the installation process to complete, and halt the guest.
  while(True):
    time.sleep(10)
    result = general.shell_exec("virsh list")
    if (hostname not in result):
      print "Now installed"
      break

  # Autostart guests.
  general.shell_exec("virsh autostart " + hostname)
  general.shell_exec("virsh start " + hostname)

  general.shell_exec("service nfs stop")
  general.shell_exec("service portmap stop")
  general.set_config_property("/etc/exports", '^' + app.SYCO_PATH + 'var/kickstart/generated.*$', "")
  general.set_config_property("/etc/exports", '^/media/dvd/.*$', "")
  general.shell_exec("umount /media/dvd")
  remove_temporary_nfs_iptables_rules()

def add_temporary_nfs_iptables_rules():
  '''
  Open iptables for NFS just during the installation.
  
  '''
  app.print_verbose("Setup iptables for nfs")
  remove_temporary_nfs_iptables_rules()

  iptables("-N guest_installation")
  iptables("-A guest_installation -m state --state NEW -p tcp --dport 32803 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p tcp --dport 32769 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p tcp --dport 892 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p tcp --dport 875 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p tcp --dport 662 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p tcp --dport 2020 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p tcp --dport 2049 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p tcp --dport 111 -j ACCEPT")

  iptables("-A guest_installation -m state --state NEW -p udp --dport 32803 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p udp --dport 32769 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p udp --dport 892 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p udp --dport 875 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p udp --dport 662 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p udp --dport 2020 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p udp --dport 2049 -j ACCEPT")
  iptables("-A guest_installation -m state --state NEW -p udp --dport 111 -j ACCEPT")

  iptables("-I INPUT  -p ALL -j guest_installation")
  iptables("-I OUTPUT -p ALL -j guest_installation")

def remove_temporary_nfs_iptables_rules():
  iptables("-F guest_installation")
  iptables("-X guest_installation")
  iptables("-D INPUT  -p ALL -j guest_installation")
  iptables("-D OUTPUT -p ALL -j guest_installation")

def configure_nfs_with_static_ip():
  '''
  # http://www.cyberciti.biz/faq/centos-fedora-rhel-iptables-open-nfs-server-ports/
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

def restart_all_nfs_services():
  general.shell_exec("service portmap restart")
  general.shell_exec("service nfs restart")
  general.shell_exec("service rpcsvcgssd restart")