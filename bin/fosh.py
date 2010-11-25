#! /usr/bin/env python

import os, sys
from optparse import OptionParser

sys.path.append(sys.path[0] + "/fosh")

from foshInstallKvmHost import InstallKvmHost

import iptables, vir, app
from general import *

def main():
  '''
  First function called when using the script. 
  Used to control the command line options, and the flow of the 
  fosh script.
  '''
  usage = "usage: %prog [options] command\n"
  usage += "commands\n"
  usage += "   install-fosh - Install the fosh script on the current server.\n" 
  usage += "   install-kvmhost - Install everything needed for the kvm host.\n" 
  usage += "   vir-rm [server] - Remove virtual server\n" 
  usage += "   fw-clear - Clear all rules from iptables" 
  
  app.parser = OptionParser(usage, version="%prog " + app.version)
  app.parser.add_option("-v", "--verbose", action="store_const", const=1, dest="verbose", default=1)
  app.parser.add_option("-q", "--quiet",   action="store_const", const=0, dest="verbose")
  
  (app.options, args) = app.parser.parse_args()
  
  app.print_verbose(app.parser.get_version())
  
  if len(args) < 1 and 2 > len(args):
    app.parser.error("Incorrect number of arguments")
  else:            
    execute_command(args)

def execute_command(args):
  '''
  Handles the control flow of the different commands.
  '''
  command = args[0].lower();
  if len(args) >= 2:
    command2 = args[1].lower();
  
  if (command == 'install-fosh'):
    install_fosh()
    
  elif (command == 'install-kvmhost'):
    obj = install_kvm_host()
    obj.run()
    
  elif (command == 'vir-rm'):
    vir_rm(command2)
    
  elif (command == 'fw-clear'):
    iptables.fw_clear()
    
  else:
    app.parser.error('Unknown command %s' % command)
               
def install_fosh():
  '''
  Install/configure this script on the current computer.
  '''
  app.print_verbose("Install fosh")
  if (os.access('/sbin/fosh', os.F_OK) == False):
    app.print_verbose("Create symlink /sbin/fosh")
    os.symlink(sys.path[0] + '/fosh.py', '/sbin/fosh')
  else:
    app.print_info("Already installed")
            
if __name__ == "__main__":
    main()