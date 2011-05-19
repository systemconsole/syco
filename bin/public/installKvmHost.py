#!/usr/bin/env python
'''
Install the server to act as a KVM host.

Read more:
http://www.linuxjournal.com/article/9764
http://www.redhat.com/promo/rhelonrhev/?intcmp=70160000000IUtyAAG
http://wiki.centos.org/HowTos/KVM
http://www.howtoforge.com/virtualization-with-kvm-on-a-fedora-11-server
http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/5/html-single/Virtualization/
http://www.cyberciti.biz/faq/centos-rhel-linux-kvm-virtulization-tutorial/

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os, re, time
import app, general, version
import net, iptables
# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 3

def build_commands(commands):
  commands.add("install-kvmhost", install_kvmhost, help="Install kvm host on the current server.")

def install_kvmhost(args):
  '''
  The actual installation of the kvm host.

  '''
  app.print_verbose("Install kvm host version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallKvmHost", SCRIPT_VERSION)
  version_obj.check_executed()

  if (not general.grep("/proc/cpuinfo", "vmx|svm")):
    app.print_error("CPU don't support virtualization.")
    _abort_kvm_host_installation()
    return

  _create_kvm_snapshot_partition()

  # Install the kvm packages
  general.shell_exec("yum -qy install kvm.x86_64")

  # Required in combination with a new kvm/cobbler/koan version.
  # This is installed from epel, and feels like it shouldn't
  # be required. Shouldn't everything be included in the kvm.x86_64
  general.shell_exec("yum -qy install qemu.x86_64")

  # Provides the virt-install command for creating virtual machines.
  general.shell_exec("yum -qy install python-virtinst")

  # Start virsh
  general.shell_exec("service libvirtd start")

  # Looks like we need to wait for the libvirtd to start, otherwise
  # the virsh nodeinfo below doesn't work.
  time.sleep(1)

  # Set selinux
  general.shell_exec("setenforce 1")

  # Is virsh started?
  result = general.shell_exec("virsh nodeinfo")
  if "CPU model:           x86_64" not in result:
    app.print_error("virsh not installed.")
    _abort_kvm_host_installation()
    return

  result = general.shell_exec("virsh -c qemu:///system list")
  if "Id Name" not in result:
    app.print_error("virsh not installed.")
    _abort_kvm_host_installation()
    return

  # todo: Might fix mouse problems in the host when viewing through VNC.
  # export SDL_VIDEO_X11_DGAMOUSE=0

  #
  # Setup bridged network
  #

  # First remove the virbr0, "NAT-interface".
  # http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization/chap-Virtualization-Network_Configuration.html
  general.shell_exec("virsh net-destroy default")

  # https://fedorahosted.org/cobbler/wiki/VirtNetworkingSetupForUseWithKoan
  # http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization/sect-Virtualization-Network_Configuration-Bridged_networking_with_libvirt.html

  # Install network bridge
  general.shell_exec("yum -y install bridge-utils")

  # Setup /etc/sysconfig/network-scripts/ifcfg-eth1
  hwaddr = _get_config_value("/etc/sysconfig/network-scripts/ifcfg-eth1", "HWADDR")
  _store_file("/etc/sysconfig/network-scripts/ifcfg-bond0",
    'DEVICE=bond0' + "\n" +
    'BONDING_OPTS="miimon=100 mode=1"' + "\n" +
    'ONPARENT=yes' + "\n" +
    'BOOTPROTO=none' + "\n" +
    'BRIDGE=br1')

  # Setup /etc/sysconfig/network-scripts/ifcfg-br1
  _store_file("/etc/sysconfig/network-scripts/ifcfg-br1",
    "DEVICE=br1" + "\n" +
    "TYPE=Bridge" + "\n" +
    "BOOTPROTO=static" + "\n" +
    "ONBOOT=yes" + "\n" +
    "IPADDR=" + net.get_lan_ip() + "\n" +
    "NETMASK=255.255.0.0" + "\n" +
    "GATEWAY=" + app.get_gateway_server_ip() + "\n" +
    "DNS1=" + app.config.get_first_dns_resolver() + "\n" +
    "DNS2=8.8.8.8")

  iptables.add_kvm_chain()
  iptables.save()

  version_obj.mark_executed()

  # Set selinux
  general.shell_exec("reboot")

  # Wait for the reboot to be executed, so the script
  # doesn't proceed to next command in install.cfg
  time.sleep(1000)

def _create_kvm_snapshot_partition():
  '''
  Create a partion that will be used by kvm/qemu to store guest snapshots.

  Memory snapshots when rebooting and such.

  TODO: Size should be equal to RAM.
  '''
  result = general.shell_exec("lvdisplay -v /dev/VolGroup00/qemu")
  if ("/dev/VolGroup00/qemu" not in result):
    general.shell_exec("lvcreate -n qemu -L 100G VolGroup00")
    general.shell_exec("mke2fs -j /dev/VolGroup00/qemu")
    general.shell_exec("mkdir /var/lib/libvirt/qemu")
    general.shell_exec("mount /dev/VolGroup00/qemu /var/lib/libvirt/qemu")
    general.shell_exec("chcon -R system_u:object_r:qemu_var_run_t:s0 /var/lib/libvirt/qemu")

    # Automount the new partion when rebooting.
    value = "/dev/VolGroup00/qemu    /var/lib/libvirt/qemu   ext3    defaults        1 2"
    general.set_config_property("/etc/fstab", value, value)

def _get_config_value(file_name, config_name):
  '''
  Get a value from an option in a config file.
  '''
  prog = re.compile("[\s]*" + config_name + "[:=\s]*(.*)")
  for line in open(file_name):
    m = prog.search(line)
    if m:
      return m.group(1)
  return False

def _store_file(file_name, value):
  '''
  Store a text in a file.
  '''
  app.print_verbose("storing file " + file_name)
  FILE = open(file_name, "w")
  FILE.writelines(value)
  FILE.close()

def _abort_kvm_host_installation():
  '''
  Write error message for aborting the installation.
  '''
  app.print_error("abort kvm host installation")
