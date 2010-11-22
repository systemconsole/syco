#! /usr/bin/env python

import os, glob, subprocess, shlex

from foshInstallKvmHost import InstallKvmHost

from optparse import OptionParser

#Constants
BOLD = "\033[1m"
RESET = "\033[0;0m"

def main():
  usage = "usage: %prog [options] command\n"
  usage += "commands\n"
  usage += "   install fosh - Install the fosh script on the current server.\n" 
  usage += "   install kvmhost - Install everything needed for the kvm host.\n" 
  usage += "   vir-rm [server] - Remove virtual server\n" 
  usage += "   fw-clear - Clear all rules from iptables\n" 
  
  parser = OptionParser(usage)
  parser.add_option("-f", "--file", dest="filename",
    help="read data from FILENAME")
  parser.add_option("-v", "--verbose",
    action="store_true", dest="verbose")
  parser.add_option("-q", "--quiet",
    action="store_false", dest="verbose")
  
  (options, args) = parser.parse_args()
  if len(args) < 1 and 2 > len(args):
    parser.error("incorrect number of arguments")
  if options.verbose:
    print "reading %s..." % options.filename
  
  executeCommand(args)

def executeCommand(args):
  command = args[0].lower();
  command2 = args[1].lower();
  if (command == 'install' and command2 == 'fosh'):
    installSelf()
    
  if (command == 'install' and command2 == 'kvmhost'):
    obj = InstallKvmHost()
    obj.run()
    
  elif (command == 'vir-rm'):
    vir_rm(args[1])
    
  elif (command == 'fw-clear'):
    fw_clear()
    
  else:
    print 'Unknown command %s' % command   
               
def installSelf():
  if (os.access('/sbin/fosh', os.F_OK) == False):
    print "Create symlink /sbin/fosh"
    os.symlink('/opt/fareoffice/bin/fosh.py', '/sbin/fosh')
  else:
    print "Already installed"
            
def remove_file(path):
  for fileName in glob.glob(path):
    print('Remove file %s' % fileName)
    os.remove('%s' % fileName)
        
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

def iptables(args):
  if (subprocess.call("/sbin/iptables " + args, shell=True)):
    print(BOLD + "Warning: " + RESET + "Iptables invalid returncode: " + retcode)
        
def fw_clear():
  print("Clear all iptables rules")
  # reset the default policies in the filter table.
  iptables("-P INPUT ACCEPT")
  iptables("-P FORWARD ACCEPT")
  iptables("-P OUTPUT ACCEPT")
  
  # reset the default policies in the nat table.
  iptables("-t nat -P PREROUTING ACCEPT")
  iptables("-t nat -P POSTROUTING ACCEPT")
  iptables("-t nat -P OUTPUT ACCEPT")
  
  # reset the default policies in the mangle table.
  iptables("-t mangle -P PREROUTING ACCEPT")
  iptables("-t mangle -P POSTROUTING ACCEPT")
  iptables("-t mangle -P INPUT ACCEPT")
  iptables("-t mangle -P OUTPUT ACCEPT")
  iptables("-t mangle -P FORWARD ACCEPT")
  
  # Flush all chains
  iptables("-F -t filter")
  iptables("-F -t nat")
  iptables("-F -t mangle")
  
  # Delete all user-defined chains
  iptables("-X -t filter")
  iptables("-X -t nat")
  iptables("-X -t mangle")
  
  # Zero all counters
  iptables("-Z -t filter")
  iptables("-Z -t nat")
  iptables("-Z -t mangle")
                    
if __name__ == "__main__":
    main()