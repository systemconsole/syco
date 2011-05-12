#!/usr/bin/env python
'''
Install all KVM guest defined for this server in etc/install.cfg

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
  commands.add("install-guests", install_guests, "guestname", help="Install all KVM guest defined for this server in install.cfg.")

def install_guests(args):
  '''

  '''
  # Set what guests that should be installed.
  guest_host_names = []
  if (len(args) == 2):
    guest_host_names.append(args[1])
  else:
    host_name=socket.gethostname()
    guest_host_names += app.get_guests(host_name)

  if (len(guest_host_names) <= 0):
    app.print_error("No guests to install.")
    return

  general.shell_exec("yum -y install koan")

  # Wait to install guests until installation sterver is alive.
  while (not is_installation_server_alive()):
    app.print_error("installation server is not alive, will try again in 15 seconds.")
    time.sleep(15)

  # Start the installation.
  guests=[]
  for guest_name in guest_host_names:
    if (_is_guest_installed(guest_name, options="")):
      app.print_verbose(guest_name + " already installed", 2)
    else:
      _install_guest(guest_name)
      guests.append(guest_name)

  # Wait for the installation process to finish,
  # And start the quests.
  app.print_verbose("Wait until all servers are installed.")
  while(len(guests)):
    time.sleep(30)

    for guest_name in guests:
      if (_start_guest(guest_name)):
        guests.remove(guest_name)

def _install_guest(guest_name):
  app.print_verbose("Install " + guest_name)

  # Create the data lvm volumegroup
  # TODO: Do we need error=False result, err=general.shell_exec("lvdisplay -v /dev/VolGroup00/" + guest_name, error=False)
  result = general.shell_exec("lvdisplay -v /dev/VolGroup00/" + guest_name)
  if ("/dev/VolGroup00/" + guest_name not in result):
    disk_var_size=int(app.get_disk_var(guest_name))
    disk_used_by_other_log_vol=15
    extra_not_used_space=5
    vol_group_size=disk_var_size+disk_used_by_other_log_vol+extra_not_used_space
    general.shell_exec("lvcreate -n " + guest_name + " -L " + str(vol_group_size) + "G VolGroup00")

  general.shell_exec("koan --server=" + app.get_installation_server_ip() + " --virt --system=" + guest_name)
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

def is_installation_server_alive():
  return general.is_server_alive(app.get_installation_server_ip(), 22)
