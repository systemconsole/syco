#!/usr/bin/env python
'''
Install a KVM guest from DVD instead of cobbler, that most syco servers uses
for installation.

This script should be executed directly on a kvm host.

WARNING:
Because of a bug in redhat/Centos it's required to have a DHCP server
during the kickstart installation. Even though we use a static ip.
Use "syco install-dhcp-server" before and "syco uninstall-dhcp-server" after
you run this script.

https://bugzilla.redhat.com/show_bug.cgi?id=392021

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
import nfs

def build_commands(commands):
  commands.add("install-guest", install_guest, "hostname, ip", help="Install kvm guest from dvd, without cobbler (reguire dhcp).")

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
  nfs.add_export("kickstart", app.SYCO_PATH + "var/kickstart/generated/")
  nfs.add_export("dvd", "/media/dvd/")
  nfs.configure_with_static_ip()
  nfs.restart_services()
  nfs.add_iptables_rules()

  # Create the data lvm volumegroup
  result = general.shell_exec("lvdisplay -v /dev/VolGroup00/" + hostname)
  if ("/dev/VolGroup00/" + hostname not in result):
    general.shell_exec("lvcreate -n " + hostname + " -L 100G VolGroup00")

  # Create the KVM image
  local_ip = net.get_lan_ip()
  general.shell_exec("virt-install --connect qemu:///system --name " + hostname + " --ram 2048 --vcpus=2 " +
    "--disk path=/dev/VolGroup00/" + hostname + " " +
    "--location nfs:" + local_ip + ":/exports/dvd " +
    "--vnc --noautoconsole --hvm --accelerate " +
    "--check-cpu " +
    "--os-type linux --os-variant=rhel5.4 " +
    "--network bridge:br1 " +
    '-x "ks=nfs:' + local_ip + ":/exports/kickstart/" + hostname + ".ks" + '"')

  # Waiting for the installation process to complete, and halt the guest.
  app.print_verbose("Wait for " + hostname + " server to be installed.", new_line=False)
  while(True):
    time.sleep(10)
    print ".",
    sys.stdout.flush()
    result = general.shell_exec("virsh list", output=False)
    if (hostname not in result):
      print "Now installed"
      break


  # Autostart guests.
  general.shell_exec("virsh autostart " + hostname)
  general.shell_exec("virsh start " + hostname)

  nfs.remove_iptables_rules()
  nfs.stop_services()
  nfs.remove_export("kickstart")
  nfs.remove_export('dvd')

  general.shell_exec("umount /media/dvd")