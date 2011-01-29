#!/usr/bin/env python
'''
Install and configure fosh to be used on localhost.
  
Changelog:
  2011-01-29 - Daniel Lindh - Adding file header and comments
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel.lindh@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os, sys
import app

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("install-fosh", install_fosh, help="Install the fosh script on the current server.")
  
def install_fosh(args):
  '''
  Install/configure this script on the current computer.
  
  '''
  app.print_verbose("Install fosh")
  if (os.access('/sbin/fosh', os.F_OK) == False):
    app.print_verbose("Create symlink /sbin/fosh")
    os.symlink(sys.path[0] + '/fosh.py', '/sbin/fosh')
  else:
    app.print_verbose("   Already installed")      
  
