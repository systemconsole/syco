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
import disk

def build_commands(commands):
  commands.add("install-guests", install_guests, "guestname", help="Install all KVM guest defined for this server in install.cfg.")

def install_guests(args):
  '''

  '''
  guest_hostnames = get_hosts_to_install(args)

  install.epel_repo()
  install.package("koan")
  install.package("python-ethtool")
  _patch_bug_in_koan()

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

def _patch_bug_in_koan():
  '''
  Apply bug fix to koan, fixed in later koan version.
  https://github.com/cobbler/cobbler/commit/0db6b7dd829cc0e9c86411390267fea927021b2f

  '''
  if "koan-2.2.3-2.el6.noarch" in x("rpm -q koan") :
    install.package("patch")
    x(
      "patch -N /usr/lib/python2.6/site-packages/koan/virtinstall.py < %s/%s" %
      (app.SYCO_VAR_PATH, "koan/virtinstall.py.patch")
    )

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

  # + 1 because it looks like the guest os needs a little bit more space
  # than it uses inside the guest. Could proably be optimized, and lowered
  # maybe just a few MB..
  disk.create_lvm_volumegroup(
      guest_name,
      int(config.host(guest_name).get_total_disk_gb()) + 1,
      config.host(guest_name).get_vol_group())

  x(
    "koan --server=" + config.general.get_installation_server_ip() +
    " --system=" + guest_name +
    " --virt -v --static-interface=eth1")

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
