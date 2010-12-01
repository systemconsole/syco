#! /usr/bin/env python

import os, sys
from optparse import OptionParser

sys.path.append(sys.path[0] + "/fosh")
sys.path.append(sys.path[0] + "/fosh/utils")

import app
import remoteInstall, installKvmHost, foTpInstall, hardening, vir, iptables, git

def main():
  '''
  First function called when using the script. 
  Used to control the command line options, and the flow of the 
  fosh script.
  '''
  usage = "usage: %prog [options] command\n"
  usage += "commands\n"
  usage += "   install-fosh          Install the fosh script on the current server.\n"
  usage += "   remote-install        Connect to all servers, and run all commands defined in install.cfg.\n"  
  usage += "   install-kvmhost       Install kvm host on the current server.\n"
  usage += "   install-fo-tp-install Install kvm guest for fo-tp-install.\n"
  usage += "   hardening             Hardening the host, removing not used software etc.\n"
  usage += "   vir-rm [server]       Remove virtual server\n"
  usage += "   iptables-clear        Clear all rules from iptables\n"
  usage += "   git-commit [comment]  Commit changes to fosh to github"  
  
  app.parser = OptionParser(usage, version="%prog " + app.version)
  app.parser.add_option("-v", "--verbose", action="store_const", const=2, dest="verbose", default=1)
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

  elif (command == 'remote-install'):
    obj = remoteInstall.RemoteInstall()
    obj.run()    
    
  elif (command == 'install-kvmhost'):
    obj = installKvmHost.InstallKvmHost()
    obj.run()
    
  elif (command == 'install-fo-tp-install'):
    foTpInstall.run()
    
  elif (command == 'hardening'):
    hardening.run()
    
  elif (command == 'vir-rm'):
    vir.vir_rm(command2)
    
  elif (command == 'iptables-clear'):
    iptables.clear()
    
  elif (command == 'git-commit'):
    git.git_commit(command2)
        
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
    app.print_verbose("   Already installed")
            
if __name__ == "__main__":    
    main()