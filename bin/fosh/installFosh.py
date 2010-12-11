#! /usr/bin/env python

import os
import app

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def get_help():
  '''
  Return short help about this module.
  
  Used by main scritpt.
  
  '''
  command="install-fosh"
  help="Install the fosh script on the current server."
  return command, help  
  
def run(args):
  '''
  Install/configure this script on the current computer.
  
  '''
  app.print_verbose("Install fosh")
  if (os.access('/sbin/fosh', os.F_OK) == False):
    app.print_verbose("Create symlink /sbin/fosh")
    os.symlink(sys.path[0] + '/fosh.py', '/sbin/fosh')
  else:
    app.print_verbose("   Already installed")      
  
