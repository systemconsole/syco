#!/usr/bin/env python
'''
Install Nmap.

Read more
http://nmap.org

'''

__author__ = "anders@televerket.net, daniel@cybercow.se"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

from general import x
from scopen import scOpen
import app
import config
import version


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("install-nmap",   install_nmap,   help="Install NMAP security scanner.")
    commands.add("uninstall-nmap", uninstall_nmap, help="Uninstall NMAP security scanner.")


def install_nmap(args):
    '''
    Install and configure nmap on the local host.

    '''
    app.print_verbose("Install NMAP version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallNMAP", SCRIPT_VERSION)
    version_obj.check_executed()

    subnet = config.general.get_subnet()
    if not subnet:
        raise('Need to put network.subnet in install.cfg')

    # Install the nmap packages.
    if os.path.exists('/usr/bin/nmap'):
        x("yum -y install nmap")

    # Setup needed folders
    x("mkdir -p /var/lib/nmap/scans")

    # Script should be executed once every hour.
    fn = "/etc/cron.daily/nmap-scan.sh"
    x("cp -f {0}var/nmap/nmap-scan.sh {1}".format(app.SYCO_PATH, fn))
    x("chmod +x {0}".format(fn))
    nmapScan = scOpen(fn)
    nmapScan.replace("${NMAP_TARGETS}", subnet)

    version_obj.mark_executed()


def uninstall_nmap(args):
  '''
  Uninstall nmap

  '''
  x("yum -y remove nmap")
  x("rm /var/lib/nmap/do_nmap_scan.sh")
  x("rm /etc/cron.weekly/nmap_cron")

  version_obj = version.Version("InstallNMAP", SCRIPT_VERSION)
  version_obj.mark_uninstalled()
