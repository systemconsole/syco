#! /usr/bin/env python

import socket, shutil, time, os
import app, general, version, iptablesClear, installCobbler

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def get_help():
  '''
  Return short help about this module.
  
  Used by main scritpt.
  '''
  command="install-guests"        
  help="Install guests on host defined in install.cfg."
  return command, help
               
def run(args):
  '''
  
  '''
  installCobbler.install_epel_repo()
  general.shell_exec("yum -y install koan")

  # Wait to install guests until fo-tp-install is alive.
  while (not installCobbler.is_fo_tp_install_alive()):
    app.print_error("fo-tp-install is not alive, try again in 15 seconds.")
    time.sleep(15)

  guests={}
  installed={}
  host_name=socket.gethostname()
  for guest_name in app.get_guests(host_name):
    if (_is_guest_installed(guest_name, options="")):
      app.print_verbose(guest_name + " already installed", 2)
    else:
      guests[guest_name]= host_name
            
  for guest_name, host_name in guests.items():
    if (not _is_guest_installed(guest_name)):
      install_guest(host_name, guest_name)
        
  # Wait for the installation process to finish,
  # And start the quests.  
  while(len(guests)):    
    time.sleep(30)
  
    for guest_name, host_name in guests.items():
      if (_start_guest(guest_name)):
        del guests[guest_name]
              
def install_guest(host_name, guest_name):
  app.print_verbose("Install " + guest_name + " on " + host_name)

  # Create the data lvm volumegroup
  result, err=general.shell_exec("lvdisplay -v /dev/VolGroup00/" + guest_name, error=False)
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
  result, err = general.shell_exec("virsh list " + options)
  if (guest_name in result):    
    return True
  else:
    return False  
        
def is_fo_tp_install_alive():
  return general.is_server_alive("10.100.100.200", 22)  