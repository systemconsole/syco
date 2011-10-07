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
    self.init_commandline_args(args)
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
    # The size of the var volume/partion.
    self.disk_var_gb = app.get_disk_var(self.hostname)
    self.disk_var_mb = str(int(self.disk_var_gb) * 1024)

    # Total size of all volumes/partions, the size of the
    # lvm volume on the host.
    self.total_disk_gb = str(int(self.disk_var_gb) + 16)

    # The total size of the physical volume in the guest.
    self.total_disk_mb = str(int(self.total_disk_gb) * 1000)

    # The ip connected to the admin net, from which the nfs
    # export is done.
    self.kvm_host_back_ip = net.get_lan_ip()

    self.ram = str(app.get_ram(self.hostname))
    self.cpu = str(app.get_cpu(self.hostname))

    self.property_list = self.get_kickstart_options()

  def get_kickstart_options(self):
    '''
    Properties that will be used to replace ${XXX} vars in kickstart file.

    '''
    prop = {}
    prop[HOSTNAME] = self.hostname
    prop[FRONT_IP] = app.get_front_ip(self.hostname)
    prop[FRONT_NETMASK] = app.get_front_netmask()
    prop[FRONT_GATEWAY] = app.get_front_gateway()
    prop[FRONT_NAMESERVER] = app.config.get_external_dns_resolver()

    prop[BACK_IP] = app.get_back_ip(self.hostname)
    prop[BACK_NETMASK] = app.get_back_netmask()
    prop[BACK_GATEWAY] = app.get_back_gateway()
    prop[BACK_NAMESERVER] = app.options.get_internal_dns_resolvers()

    prop[ROOT_PASSWORD] = app.get_root_password_hash()

    prop[DISK_VAR_MB] = self.disk_var_mb
    prop[TOTAL_DISK_MB] = self.total_disk_mb
    return prop

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

      set_config_property_batch(hostname_ks_file, self.property_list)

  def start_nfs_export(self):
      nfs.add_export("kickstart", app.SYCO_PATH + "var/kickstart/generated/")
      nfs.add_export("dvd", "/media/dvd/")
      nfs.configure_with_static_ip()
      nfs.restart_services()
      nfs.add_iptables_rules()

  def stop_nfs_export(self):
      nfs.remove_iptables_rules()
      nfs.stop_services()
      nfs.remove_export("kickstart")
      nfs.remove_export('dvd')

  def create_kvm_host():
      self.create_lvm_volumegroup()

      shell_exec(
        "virt-install -d --connect qemu:///system --name " + self.hostname +
        " --ram " + self.ram +
        " --vcpus=" + self.cpu + " --cpuset=auto" +
        " --disk path=/dev/VolGroup00/" + self.hostname +
        " --location nfs:" + self.kvm_host_back_ip + ":/dvd" +
        " --vnc --noautoconsole --hvm --accelerate" +
        " --check-cpu" +
        " --os-type linux --os-variant=rhel6" +
        " --network bridge:br0" +
        " --network bridge:br1" +
        ' -x "ks=nfs:' + self.kvm_host_back_ip + ':/kickstart/' + self.hostname + '.ks'
        ' ksdevice=eth1' +
        ' ip=' + self.property_list['BACK_IP'] +
        ' netmask=' + self.property_list['BACK_NETMASK'] +
        ' dns=' + self.property_list['BACK_NAMESERVER'] +
        ' gateway=' +  + self.property_list['BACK_GATEWAY'])

      self.wait_for_installation_to_complete()
      self.autostart_guests()

  def create_lvm_volumegroup(self):
    result = shell_exec("lvdisplay -v /dev/VolGroup00/" + self.hostname)
    if ("/dev/VolGroup00/" + self.hostname not in result):
      shell_exec("lvcreate -n " + self.hostname +
                 " -L " + self.total_disk_gb + "G VolGroup00")

  def wait_for_installation_to_complete():
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
      if (hostname not in result):
        print "Now installed"
        break

  def autostart_guests(self):
    # Autostart guests.
    shell_exec("virsh autostart " + self.hostname)
    shell_exec("virsh start " + self.hostname)
