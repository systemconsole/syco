******************************************************************************
NOTICE TO USERS WARNING!
The use of this system is restricted to authorized users, unauthorized access
is forbidden and will be prosecuted by law. All information and communications
on this system are subject to review, monitoring and recording at any time,
without notice or permission. Users should have no expectation of privacy.
******************************************************************************
#!/usr/bin/env python
'''
Installs clam antivirus

Read more:
  http://wiki.mattrude.com/ClamAV

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Mattias Hemingsson"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


# Path to clam installation.

import app
from general import x, urlretrive
import config
from scopen import scOpen
import version


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 2


def build_commands(commands):
  commands.add("install-david", install_david, help="Install David.")
  commands.add("remove-david", remove_david, help="Remove David.")

def install_david(args):
  app.print_verbose("Install David (Fresh install of David).")
  x("yum -y install iptraf")

def remove_david(args):
  app.print_verbose("Removing david functions")
  x("yum -y remove iptraf")
