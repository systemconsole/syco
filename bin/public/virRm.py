#! /usr/bin/env python

import general, app, version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("vir-rm", vir_rm, "[server]", help="Remove virtual server")
  
def vir_rm(args):
  server_name=args[1]
  app.print_verbose('Remove virtual server %s.' % server_name)
    
  app.print_verbose("Destory the kvm instance");
  general.shell_exec("virsh destroy " + server_name)
                  
  general.remove_file('/etc/libvirt/qemu/autostart/%s.xml' % server_name)        
  general.remove_file('/etc/libvirt/qemu/%s.xml' % server_name)
  general.remove_file('/opt/fareoffice/var/virtstorage/' + server_name +'*')
  general.remove_file('/var/log/libvirt/qemu/%s.log*' % server_name)
  general.shell_exec("updatedb")
  
  general.shell_exec("lvremove -f /dev/VolGroup00/" + server_name)  
  
  app.print_verbose("Restart libvirtd");
  general.shell_exec("/etc/init.d/libvirtd restart")

