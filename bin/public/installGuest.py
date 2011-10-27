#!/usr/bin/env python
'''
Install all KVM guest defined for this server in install.cfg.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import socket
import time
import app
import config
import general
from general import x
import install
import installCobbler

def build_commands(commands):
  commands.add("install-guests", install_guests, "guestname", help="Install all KVM guest defined for this server in install.cfg.")

def install_guests(args):
  '''

  '''
  guest_hostnames = get_hosts_to_install(args)

  install.epel_repo()
  install.package("koan")

  # Wait to install guests until installation server is alive.
  wait_for_installation_server_to_start()

  guests = start_installation(guest_hostnames)
  wait_for_installation_to_complete(guests)

def get_hosts_to_install(args):
  # Set what guests that should be installed.
  guest_hostnames = []
  if (len(args) == 2):
    guest_hostnames.append(args[1])
  else:
    hostname = socket.gethostname()
    guest_hostnames += config.host(hostname).get_guests()

  if (len(guest_hostnames) <= 0):
    raise Exception("No guests to install.")

  return guest_hostnames

def start_installation(guest_hostnames):
  '''
  Start parallell installation of all guests defined in guest_hostnames.

  '''
  guests=[]
  for guest_name in guest_hostnames:
    if (_is_guest_installed(guest_name, options="--all")):
      app.print_verbose(guest_name + " already installed", 2)
    else:
      _install_guest(guest_name)
      guests.append(guest_name)
  return guests

def wait_for_installation_to_complete(guests):
  '''
  Wait for the installation process to finish, and start the quests.

  '''
  app.print_verbose("Wait until all servers are installed.")
  while(len(guests)):
    time.sleep(30)

    for guest_name in guests:
      if (_start_guest(guest_name)):
        guests.remove(guest_name)

def _install_guest(guest_name):
  '''
  Create lvm vol and install guest with koan.

  '''
  app.print_verbose("Install " + guest_name)

  # Create the data lvm volumegroup
  # TODO: Do we need error=False result, err=x("lvdisplay -v /dev/VolGroup00/" + guest_name, error=False)
  result = x("lvdisplay -v /dev/VolGroup00/" + guest_name)
  if ("/dev/VolGroup00/" + guest_name not in result):
    vol_group_size=int()
    x("lvcreate -n " + guest_name +
                       " -L " + config.host(guest_name).get_total_disk_gb() +
                       "G VolGroup00")

  x(
    "koan --server=" + config.general.get_installation_server_ip() +
    " --system=" + guest_name +
    " --virt -v --static-interface=eth0")

  x("virsh autostart " + guest_name)

def _start_guest(guest_name):
  '''
  Wait for guest to be halted, before starting it.

  '''
  if (_is_guest_installed(guest_name, options="")):
    return False
  else:
    x("virsh start " + guest_name)
    return True

def _is_guest_installed(guest_name, options=""):
  '''
  Is the guest already installed on the kvm host.

  '''
  result = x("virsh list " + options)
  if (guest_name in result):
    return True
  else:
    return False

def wait_for_installation_server_to_start():
  '''
  Todo: Check on the cobbler werb repo folder instead of port 22.
        Install something with refresh_repo

  '''
  general.wait_for_server_to_start(config.general.get_installation_server_ip(), 22)
