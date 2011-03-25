#!/usr/bin/env python
'''
Install a KVM guest that should be used as an installation server.

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
  general.shell_exec("service portmap restart")
  general.shell_exec("service nfs restart")

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
    '-x "ks=nfs:" + local_ip + ":' + ks_path)

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
  general.set_config_property("/etc/exports", '^' + app.SYCO_PATH + 'var/.*$', "")
  general.set_config_property("/etc/exports", '^/media/dvd/.*$', "")
  general.shell_exec("umount /media/dvd")
