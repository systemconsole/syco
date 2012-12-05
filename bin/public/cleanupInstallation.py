#!/usr/bin/env python
'''
Close an installation

'''

__author__ = "elis.kullberg@netlight.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Testing"


import app
from hardening.ssh import setup_ssh
from yumUtils import disable_external_repos
import version

SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("cleanup-installation", cleanup_installation,  help="Hardening server")
  

def cleanup_installation(args):
    '''
    Clean up a host installation. Disabe external repos (so user needds to explicitly update external packages).
    Harden SSH. Remove temp files. 

    '''
    # Should only be run once!
    app.print_verbose("Cleanup version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("cleanup", SCRIPT_VERSION)
    version_obj.check_executed()

    # Disable external repos
    app.print_verbose("Disabling external yum repos")
    disable_external_repos()

    # Harden SSH
    app.print_verbose("Hardening SSH")
    setup_ssh()

    # Mark as successfully executed
    version_obj.mark_executed()

