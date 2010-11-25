#! /usr/bin/env python

import general

def vir_rm(serverName):
  print 'Remove virtual server %s.' % serverName
  
  print("Destory the kvm instance");
  subprocess.call(shlex.split("virsh destroy " + serverName))
                  
  remove_file('/etc/libvirt/qemu/autostart/%s.xml' % serverName)        
  remove_file('/etc/libvirt/qemu/%s.xml' % serverName)
  remove_file('/opt/fareoffice/var/virtstorage/' + serverName +'*')
  remove_file('/var/log/libvirt/qemu/%s.log*' % serverName)
  subprocess.call(["updatedb"])
  
  print("Restart libvirtd");
  subprocess.call(shlex.split("/etc/init.d/libvirtd restart"))
  #print(BOLD + "INFO: " + RESET + "Remember to run /etc/init.d/libvirtd restart")
