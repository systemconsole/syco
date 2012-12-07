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

    # Install the nmap packages.
    if not os.path.exists('/usr/bin/nmap'):
        x("yum -y install nmap")

    # Setup needed folders
    x("mkdir -p /var/lib/nmap/scans")

    add_cron(config.general.get_front_subnet(), "front")
    add_cron(config.general.get_back_subnet(), "back")

    version_obj.mark_executed()


def add_cron(targets, name):
    # Script should be executed once every hour.
    fn = "/etc/cron.daily/nmap-scan-{0}.sh".format(name)
    x("cp -f {0}var/nmap/nmap-scan.sh {1}".format(app.SYCO_PATH, fn))
    x("chmod +x {0}".format(fn))
    nmapScan = scOpen(fn)
    nmapScan.replace("${NMAP_TARGETS}", targets)
    nmapScan.replace("${NMAP_NAME}", name)


def uninstall_nmap(args):
  '''
  Uninstall nmap

  '''
  x("yum -y remove nmap")
  x("rm /var/lib/nmap/do_nmap_scan.sh")
  x("rm /etc/cron.weekly/nmap_cron")

  version_obj = version.Version("InstallNMAP", SCRIPT_VERSION)
  version_obj.mark_uninstalled()
