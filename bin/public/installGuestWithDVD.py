#!/usr/bin/env python
'''
Install a KVM guest from DVD instead of cobbler.

This will probably only be used to install the installation server that hosts
the cobbler service.

This script should be executed directly on a kvm host.

All configurations are retrived from the install.cfg.

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
import config
from general import set_config_property_batch, shell_exec
import net
import nfs
import sys

def build_commands(commands):
  commands.add(
    "install-guest", install_guest, "hostname",
    help="Install KVM guest from dvd.")

class install_guest:
  hostname = None

  def __init__(self, args):
    self.check_commandline_args(args)
    app.print_verbose("Install kvm guest " + self.hostname + ".")
    self.check_if_host_is_installed()
    self.init_host_options_from_config()

    self.mount_dvd()
    self.create_kickstart()
    self.start_nfs_export()

    self.create_kvm_host()

    self.stop_nfs_export()
    self.unmount_dvd()

  def check_commandline_args(self, args):
    if (len(args) != 2):
        raise Exception("Enter the hostname of the server to install")
    else:
      self.hostname = args[1]

  def check_if_host_is_installed(self):
    result = shell_exec("virsh list --all")
    if (self.hostname in result):
      raise Exception(self.hostname + " already installed")

  def init_host_options_from_config(self):
    '''
    Initialize all used options from install.cfg.

    If the options are invalid, app and config will throw exceptions,
    that will be forwarded to the starter app.

    '''
    # The ip connected to the admin net, from which the nfs
    # export is done.
    self.kvm_host_back_ip = net.get_lan_ip()

    self.ram = str(config.host(self.hostname).get_ram())
    self.cpu = str(config.host(self.hostname).get_cpu())

    self.set_kickstart_options()

  def set_kickstart_options(self):
    '''
    Properties that will be used to replace ${XXX} vars in kickstart file.

    '''
    prop = {}
    prop['HOSTNAME'] = self.hostname
    prop['FRONT_IP'] = config.host(self.hostname).get_front_ip()
    prop['FRONT_NETMASK'] = config.general.get_front_netmask()
    prop['FRONT_GATEWAY'] = config.general.get_front_gateway_ip()
    prop['FRONT_NAMESERVER'] = config.general.get_front_resolver_ip()

    prop['BACK_IP'] = config.host(self.hostname).get_back_ip()
    prop['BACK_NETMASK'] = config.general.get_back_netmask()
    prop['BACK_GATEWAY'] = config.general.get_back_gateway_ip()
    prop['BACK_NAMESERVER'] = config.general.get_back_resolver_ip()

    prop['ROOT_PASSWORD'] = '"' + app.get_root_password_hash() + '"'

    prop['DISK_VAR_MB'] = config.host(self.hostname).get_disk_var_mb()
    prop['TOTAL_DISK_MB'] = config.host(self.hostname).get_total_disk_mb()
    prop['TOTAL_DISK_GB'] = config.host(self.hostname).get_total_disk_gb()

    self.property_list = prop

  def mount_dvd(self):
    if (not os.access("/media/dvd", os.F_OK)):
      shell_exec("mkdir /media/dvd")

    if (not os.path.ismount("/media/dvd")):
      shell_exec("mount -o ro /dev/dvd /media/dvd")

  def unmount_dvd(self):
    shell_exec("umount /media/dvd")

  def create_kickstart(self):
      '''
      Create the kickstart file that should be used during installation.

      '''
      ks_folder = app.SYCO_PATH + "var/kickstart/generated/"
      hostname_ks_file = ks_folder + self.hostname + ".ks"
      dvd_ks_file = app.SYCO_PATH + "var/kickstart/dvd-guest.ks"

      shell_exec("mkdir -p " + ks_folder)
      shell_exec("cp " + dvd_ks_file + " " + hostname_ks_file)

      set_config_property_batch(hostname_ks_file, self.property_list, False)

  def start_nfs_export(self):
      nfs.add_export("kickstart", app.SYCO_PATH + "var/kickstart/generated/")
      nfs.add_export("dvd", "/media/dvd/")
      nfs.configure_with_static_ip()
      nfs.restart_services()
      nfs.add_iptables_rules()

  def stop_nfs_export(self):
      nfs.remove_iptables_rules()
      nfs.stop_services()
      time.sleep(1)
      nfs.remove_export("kickstart")
      nfs.remove_export('dvd')

  def create_kvm_host(self):
      self.create_lvm_volumegroup()

      cmd = "virt-install -d --connect qemu:///system"
      cmd += " --name " + self.hostname
      cmd +=  " --ram " + self.ram
      cmd +=  " --vcpus=" + self.cpu + " --cpuset=auto"
      cmd +=  " --vnc --noautoconsole"
      cmd +=  " --hvm --accelerate"
      cmd +=  " --check-cpu"
      cmd +=  " --disk path=/dev/VolGroup00/" + self.hostname
      cmd +=  " --os-type linux --os-variant=rhel6"
      cmd +=  " --network bridge:br0"
      cmd +=  " --network bridge:br1"
      cmd +=  " --location nfs:" + self.kvm_host_back_ip + ":/dvd"
      cmd +=  ' -x "ks=nfs:' + self.kvm_host_back_ip + ':/kickstart/' + self.hostname + '.ks'
      cmd +=  ' ksdevice=eth0'
      cmd +=  ' ip=' + self.property_list['BACK_IP']
      cmd +=  ' netmask=' + self.property_list['BACK_NETMASK']
      cmd +=  ' dns=' + self.kvm_host_back_ip
      cmd +=  ' gateway=' + self.kvm_host_back_ip
      cmd +=  ' "'

      shell_exec(cmd)
      self.wait_for_installation_to_complete()
      self.autostart_guests()

  def create_lvm_volumegroup(self):
    result = shell_exec("lvdisplay -v /dev/VolGroup00/" + self.hostname)
    if ("/dev/VolGroup00/" + self.hostname not in result):
      shell_exec("lvcreate -n " + self.hostname +
                 " -L " + self.property_list['TOTAL_DISK_GB'] + "G VolGroup00")

  def wait_for_installation_to_complete(self):
    '''
    Waiting for the installation process to complete, and halt the guest.

    '''
    app.print_verbose("Wait for installation of " + self.hostname +
                      " to complete", new_line=False)
    while(True):
      time.sleep(10)
      print ".",
      sys.stdout.flush()
      result = shell_exec("virsh list", output=False)
      if (self.hostname not in result):
        print "Now installed"
        break

  def autostart_guests(self):
    # Autostart guests.
    shell_exec("virsh autostart " + self.hostname)
    shell_exec("virsh start " + self.hostname)
