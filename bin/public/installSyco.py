#!/usr/bin/env python
'''
Install and configure syco to be used on localhost.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os, sys
import app

def build_commands(commands):
  commands.add("install-syco", install_syco, help="Install the syco script on the current server.")

def install_syco(args):
  '''
  Install/configure this script on the current computer.

  '''
  app.print_verbose("Install syco")
  if (os.access('/sbin/syco', os.F_OK) == False):
    app.print_verbose("Create symlink /sbin/syco")
    os.symlink(sys.path[0] + '/syco.py', '/sbin/syco')
  else:
    app.print_verbose("   Already installed")

