#!/usr/bin/env python
'''
Harden the computer by removing unnessary services, add security fixes etc.

The script is based on the CIS standard. All
functionality is separated into small modules in the hardening folder.

Read more
http://www.linuxforums.org/forum/red-hat-fedora-linux/166631-redhat-centos-hardening-customizing-removing-excess.html
http://www.nsa.gov/ia/_files/factshe...phlet-i731.pdf
http://wiki.centos.org/HowTos/OS_Protection
http://benchmarks.cisecurity.org/en-us/?route=downloads.show.single.rhel5.200

Examples:
---------
syco hardening          - Hardening the server.
syco hardening-ssh      - Hardening sshd.
syco hardening-verify   - Verify that the server is harden.

'''

__author__ = "daniel@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import app
import version

from hardening.common import setup_common
from hardening.auditd import install_auditd
from hardening.network import setup_network
from hardening.package import packages
from hardening.passwords import harden_password
from hardening.permissions import setup_permissions
from hardening.service import disable_services

from hardening.ssh import setup_ssh


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 4


def build_commands(commands):
  commands.add("hardening",          harden,  help="Hardening server")
  commands.add("hardening-ssh",      harden_ssh,  help="Hardening SSH server and client")


def harden(args):
    '''
    Harden server by running harden scrips located in hardening folder.
    Config file for scripts loctaed in syco/var/hardening

    '''
    app.print_verbose("Hardening version: %d" % SCRIPT_VERSION)

    version_obj = version.Version("hardening", SCRIPT_VERSION)
    version_obj.check_executed()

    setup_common()
    install_auditd()
    setup_network()
    packages()
    harden_password()
    setup_permissions()
    disable_services()

    version_obj.mark_executed()


def harden_ssh(args):
    '''
    Harden SSH server.

    The root account will not be able to login through SSH after the server
    is harden. This is separated in it's own command to give the admin
    a chance to add new users before locking down root.

    '''
    app.print_verbose("Harden host version: %d" % SCRIPT_VERSION)

    version_obj = version.Version("hardeningSSH", SCRIPT_VERSION)
    version_obj.check_executed()

    setup_ssh()

    version_obj.mark_executed()
