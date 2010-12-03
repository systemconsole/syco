#! /usr/bin/env python

import general, app, version

def vir_rm(server_name):
  app.print_verbose('Remove virtual server %s.' % server_name)
    
  app.print_verbose("Destory the kvm instance");
  general.shell_exec("virsh destroy " + server_name)
                  
  general.remove_file('/etc/libvirt/qemu/autostart/%s.xml' % server_name)        
  general.remove_file('/etc/libvirt/qemu/%s.xml' % server_name)
  general.remove_file('/opt/fareoffice/var/virtstorage/' + server_name +'*')
  general.remove_file('/var/log/libvirt/qemu/%s.log*' % server_name)
  general.shell_exec("updatedb")
  
  app.print_verbose("Restart libvirtd");
  general.shell_exec("/etc/init.d/libvirtd restart")