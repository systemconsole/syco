#!/usr/bin/env python
'''
Install a KVM guest that should be used as an installation server.

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

def build_commands(commands):
  commands.add("install-fo-tp-install", install_fo_tp_install, help="Install kvm guest for fo-tp-install")

# The main function
#
def install_fo_tp_install(args):
  # Is fo-tp-install already installed?
  result = general.shell_exec("virsh list --all")
  if ("fo-tp-install" in result):
    app.print_error("fo-tp-install already installed")
    return

  # Mount dvd
  if (not os.access("/media/dvd", os.F_OK)):
    general.shell_exec("mkdir /media/dvd")

  if (not os.path.ismount("/media/dvd")):
    general.shell_exec("mount -o ro /dev/dvd /media/dvd")

  # Export kickstart file
  general.set_config_property("/etc/exports", '^' + app.SYCO_PATH + 'var/.*$', app.SYCO_PATH + "var/ *(rw)")
  general.set_config_property("/etc/exports", '^/media/dvd/.*$', "/media/dvd/ *(rw)")
  general.shell_exec("service portmap restart")
  general.shell_exec("service nfs restart")

  # Create the data lvm volumegroup
  # TODO: Do we need the erro = False
  # result,err=general.shell_exec("lvdisplay -v /dev/VolGroup00/fo-tp-install", error=False)
  result = general.shell_exec("lvdisplay -v /dev/VolGroup00/fo-tp-install")
  if ("/dev/VolGroup00/fo-tp-install" not in result):
    general.shell_exec("lvcreate -n fo-tp-install -L 100G VolGroup00")

  # Create the KVM image
  general.shell_exec("virt-install --connect qemu:///system --name fo-tp-install --ram 2048 --vcpus=2 " +
    "--disk path=/dev/VolGroup00/fo-tp-install " +
    "--location nfs:10.100.100.212:/media/dvd " +
    "--vnc --noautoconsole --hvm --accelerate " +
    "--check-cpu " +
    "--os-type linux --os-variant=rhel5.4 " +
    "--network=bridge:br1 " +
    '-x "ks=nfs:10.100.100.212:' + app.SYCO_PATH + 'var/fo-tp-install.ks"')

  # Waiting for the installation process to complete, and halt the guest.
  while(True):
    time.sleep(10)
    result = general.shell_exec("virsh list")
    if ("fo-tp-install" not in result):
      print "Now installed"
      break

  # Autostart guests.
  general.shell_exec("virsh autostart fo-tp-install")
  general.shell_exec("virsh start fo-tp-install")

  general.shell_exec("service nfs stop")
  general.shell_exec("service portmap stop")
  general.set_config_property("/etc/exports", '^' + app.SYCO_PATH + 'var/.*$', "")
  general.set_config_property("/etc/exports", '^/media/dvd/.*$', "")
  general.shell_exec("umount /media/dvd")
