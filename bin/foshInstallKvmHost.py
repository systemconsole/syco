#! /usr/bin/env python

import os, subprocess, re, ConfigParser

from foshVersion import Version

class InstallKvmHost:
  verbose = True
  version = 1

  def grep(self, fileName, pattern):
    # Check if cpu can handle virtualization
    prog = re.compile(pattern)
    for line in open(fileName):
      if prog.search(line):
        return True
    return False
    
  def shellExec(self, command):
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]
    if self.verbose:
      print result
    return result

  def getConfigValue(self, fileName, configName):
    # Check if cpu can handle virtualization
    prog = re.compile("[\s]*" + configName + "[:=\s]*(.*)")
    for line in open(fileName):
      m = prog.search(line)
      if m:
        return m.group(1)
    return False    
    
  def storeFile(self, fileName, value):
    FILE = open(fileName, "w")   
    FILE.writelines(value)
    FILE.close()
  
  def run(self):
    version = Version()
    if version.isExecuted("InstallKvmHost", self.version):
      return

    if (not self.grep("/proc/cpuinfo", "vmx|svm")):
      print "ERROR: CPU don't support virtualization."
      return

    # Install the kvm packages
    self.shellExec("yum -qy install kvm.x86_64")
        
    # Provides the virt-install command for creating virtual machines.
    self.shellExec("yum -qy install python-virtinst")
        
    # Start virsh      
    self.shellExec("service libvirtd start")
          
    # Set selinux
    self.shellExec("setenforce 1")

    # Is virsh started?
    result = self.shellExec("virsh nodeinfo")
    if "CPU model:           x86_64" not in result:
      print "ERROR: virsh not installed."
      return

    result = self.shellExec("virsh -c qemu:///system list")
    if "Id Name" not in result:
      print "ERROR: virsh not installed."
      return

    #result = self.shellExec("/sbin/lsmod | grep kvm")
    #if "kvm_intel" not in result:
    #  print "ERROR: kvm_intel not installed."
    #  return

    # todo: Might fix mouse problems in the host when viewing through VNC.    
    # export SDL_VIDEO_X11_DGAMOUSE=0


    #
    # Setup bridged network
    #
      
    # First remove the virbr0, "NAT-interface".
    # http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization/chap-Virtualization-Network_Configuration.html
    self.shellExec("virsh net-destroy default")
    
    # https://fedorahosted.org/cobbler/wiki/VirtNetworkingSetupForUseWithKoan
    # http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization/sect-Virtualization-Network_Configuration-Bridged_networking_with_libvirt.html
      
    # Install network bridge
    self.shellExec("yum install bridge-utils")
      
    # Setup /etc/sysconfig/network-scripts/ifcfg-eth1
    hwaddr = self.getConfigValue("/etc/sysconfig/network-scripts/ifcfg-eth1", "HWADDR")
    self.storeFile("/etc/sysconfig/network-scripts/ifcfg-eth1",
"""DEVICE=eth1
HWADDR=%s
ONBOOT=yes
TYPE=Ethernet
IPV6INIT=no
USERCTL=no
BRIDGE=br1
BOOTPROTO=dhcp""" % hwaddr)
      
    # Setup /etc/sysconfig/network-scripts/ifcfg-br1
    self.storeFile("/etc/sysconfig/network-scripts/ifcfg-br1",
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
              
    self.shellExec("service iptables start")
    self.shellExec("iptables -I FORWARD -m physdev --physdev-is-bridged -j ACCEPT")
    self.shellExec("service iptables save")
    self.shellExec("service network restart")    

    #  
    # Create logical volume
    # This will probably be done when doning the koan installation instead.
    #
        
    # Create logical volume for images with selinux enabled.
    # http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization/sect-Virtualization-Security_for_virtualization-SELinux_and_virtualization.html
      
    # lvcreate -n data -L 5G VolGroup00
    # mke2fs -j  /dev/VolGroup00/data
    # mkdir -p /opt/fareoffice/var/virtstorage
    # mount /dev/VolGroup00/data /opt/fareoffice/var/virtstorage
    # semanage fcontext -a -t virt_image_t "/opt/fareoffice/var/virtstorage(/.*)?"
    # restorecon -R -v /opt/fareoffice/var/virtstorage
      
    # To see the change
    # tail /etc/selinux/targeted/contexts/files/file_contexts.local
    version.markExecuted("InstallKvmHost", self.version):
      
if __name__ == "__main__":
  obj = InstallKvmHost()
  obj.run()
