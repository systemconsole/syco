#!/usr/bin/env python
'''
Instal all KVM guest defined for this server in etc/install.cfg

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import socket, time
import app, general, installCobbler

def build_commands(commands):
  commands.add("install-guests", install_guests, help="Install all KVM guest defined for this server in install.cfg.")

def install_guests(args):
  '''

  '''
  installCobbler.install_epel_repo()
  general.shell_exec("yum -y install koan")

  # Wait to install guests until fo-tp-install is alive.
  while (not is_fo_tp_install_alive()):
    app.print_error("fo-tp-install is not alive, try again in 15 seconds.")
    time.sleep(15)

  guests={}
  installed={}
  host_name=socket.gethostname()
  for guest_name in app.get_guests(host_name):
    if (_is_guest_installed(guest_name, options="")):
      app.print_verbose(guest_name + " already installed", 2)
    else:
      guests[guest_name]=host_name

  for guest_name, host_name in guests.items():
    if (not _is_guest_installed(guest_name)):
      _install_guest(host_name, guest_name)

  # Wait for the installation process to finish,
  # And start the quests.
  while(len(guests)):
    time.sleep(30)

    for guest_name, host_name in guests.items():
      if (_start_guest(guest_name)):
        del guests[guest_name]

def _install_guest(host_name, guest_name):
  app.print_verbose("Install " + guest_name + " on " + host_name)

  # Create the data lvm volumegroup
  # TODO: Do we need error=False result, err=general.shell_exec("lvdisplay -v /dev/VolGroup00/" + guest_name, error=False)
  result = general.shell_exec("lvdisplay -v /dev/VolGroup00/" + guest_name)
  if ("/dev/VolGroup00/" + guest_name not in result):
    disk_var_size=int(app.get_disk_var(guest_name))
    disk_used_by_other_log_vol=15
    extra_not_used_space=5
    vol_group_size=disk_var_size+disk_used_by_other_log_vol+extra_not_used_space
    general.shell_exec("lvcreate -n " + guest_name + " -L " + str(vol_group_size) + "G VolGroup00")

  general.shell_exec("koan --server=10.100.100.200 --virt --system=" + guest_name)
  general.shell_exec("virsh autostart " + guest_name)

def _start_guest(guest_name):
  '''
  Wait for guest to be halted, before starting it.

  '''
  if (_is_guest_installed(guest_name, options="")):
    return False
  else:
    general.shell_exec("virsh start " + guest_name)
    return True

def _is_guest_installed(guest_name, options="--all"):
  '''
  Is the guest already installed on the kvm host.

  '''
  result = general.shell_exec("virsh list " + options)
  if (guest_name in result):
    return True
  else:
    return False

def is_fo_tp_install_alive():
  return general.is_server_alive("10.100.100.200", 22)
