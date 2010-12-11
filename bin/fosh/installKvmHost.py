#! /usr/bin/env python

#  Install the server to act as a kvm host.
#  
#  KVM Installation doc
#  http://www.linuxjournal.com/article/9764
#  http://www.redhat.com/promo/rhelonrhev/?intcmp=70160000000IUtyAAG
#  http://wiki.centos.org/HowTos/KVM
#  http://www.howtoforge.com/virtualization-with-kvm-on-a-fedora-11-server
#  http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/5/html-single/Virtualization/
#  http://www.cyberciti.biz/faq/centos-rhel-linux-kvm-virtulization-tutorial/  


import os, subprocess, re, ConfigParser, time
import app, general, version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 3

def build_commands(commands):
  commands.add("install-kvmhost", install_kvmhost, help="Install kvm host on the current server.")

def install_kvmhost(self):
  '''
  The actual installation of the kvm host.
  
  '''
  global script_version
  app.print_verbose("Install kvm host version: %d" % script_version)
  ver_obj = version.Version()
  if ver_obj.is_executed("InstallKvmHost", script_version):
    app.print_verbose("   Already installed latest version")
    return

  if (not general.grep("/proc/cpuinfo", "vmx|svm")):
    app.print_error("CPU don't support virtualization.")
    self._abort_kvm_host_installation()
    return

  # Install the kvm packages
  general.shell_exec("yum -qy install kvm.x86_64")
      
  # Provides the virt-install command for creating virtual machines.
  general.shell_exec("yum -qy install python-virtinst")
      
  # Start virsh      
  general.shell_exec("service libvirtd start")
        
  # Set selinux
  general.shell_exec("setenforce 1")

  # Is virsh started?
  result,err = general.shell_exec("virsh nodeinfo", os.F_OK)
  if "CPU model:           x86_64" not in result:
    app.print_error("virsh not installed.")
    self._abort_kvm_host_installation()      
    return

  result,err = general.shell_exec("virsh -c qemu:///system list")
  if "Id Name" not in result:
    app.print_error("virsh not installed.")
    self._abort_kvm_host_installation()
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
  general.shell_exec("yum install bridge-utils")
    
  # Setup /etc/sysconfig/network-scripts/ifcfg-eth1
  hwaddr = self._get_config_value("/etc/sysconfig/network-scripts/ifcfg-eth1", "HWADDR")
  self._store_file("/etc/sysconfig/network-scripts/ifcfg-eth1",
"""DEVICE=eth1
HWADDR=%s
ONBOOT=yes
TYPE=Ethernet
IPV6INIT=no
USERCTL=no
BRIDGE=br1
BOOTPROTO=dhcp""" % hwaddr)
    
  # Setup /etc/sysconfig/network-scripts/ifcfg-br1
  self._store_file("/etc/sysconfig/network-scripts/ifcfg-br1",
"""DEVICE=br1
TYPE=Bridge
BOOTPROTO=dhcp
ONBOOT=yes""")    

#      This might be an option for the bridge
#      DEVICE=br1
#      TYPE=Bridge
#      BOOTPROTO=none
#      GATEWAY=10.100.0.1
#      IPADDR=10.100.100.211
#      NETMASK=255.255.0.0
#      ONBOOT=yes

  general.shell_exec("service iptables start")
  general.shell_exec("iptables -I FORWARD -m physdev --physdev-is-bridged -j ACCEPT")
  general.shell_exec("service iptables save")
  general.shell_exec("service network restart")    

  ver_obj.mark_executed("InstallKvmHost", script_version)
  
  # Set selinux
  general.shell_exec("reboot")
  
  # Wait for the reboot to be executed, so the script
  # doesn't proceed to next command in install.cfg
  time.sleep(1000)         

def _get_config_value(self, file_name, config_name):
  '''
  Get a value from an option in a config file.
  '''
  prog = re.compile("[\s]*" + config_name + "[:=\s]*(.*)")
  for line in open(file_name):
    m = prog.search(line)
    if m:
      return m.group(1)
  return False    
  
def _store_file(self, file_name, value):
  '''
  Store a text in a file.
  '''
  app.print_verbose("storing file " + file_name)
  FILE = open(file_name, "w")   
  FILE.writelines(value)
  FILE.close()
  
def _abort_kvm_host_installation(self):
  '''
  Write error message for aborting the installation.
  '''
  app.print_error("abort kvm host installation")          