#!/usr/bin/env python
'''
Install Nmap.

Read more
http://nmap.org
'''

__author__ = "anders@televerket.net"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import fileinput, shutil, os
import app
import general
from general import x
import version
import iptables
import config
from scopen import scOpen


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-nmap",             install_nmap, help="Install NMAP security scanner.")
  commands.add("uninstall-nmap",           uninstall_nmap,           help="Uninstall NMAP security scanner.")



def install_nmap(args):
  '''
  Install and configure nmap on the local host.

  '''
  app.print_verbose("Install NMAP version: %d" % SCRIPT_VERSION)
  
  
  subnet = config.general.get_subnet()
  if not subnet:
    raise('Need to put network.subnet in install.cfg')

  version_obj = version.Version("InstallNMAP", SCRIPT_VERSION)
  version_obj.check_executed()

 


  # Install the mysql-server packages.
  if (not os.access("/usr/bin/nmap", os.W_OK|os.X_OK)):
    x("yum -y install nmap")

    if (not os.access("/usr/bin/nmap", os.F_OK)):
      raise Exception("Couldn't install NMAP")

  # Configure iptables
  x("mkdir -p /var/lib/nmap")
  x("mkdir -p /var/lib/nmap/scans")
  
  shutil.copy(app.SYCO_PATH + "var/nmap/do_nmap_scan.sh",  "/var/lib/nmap/do_nmap_scan.sh")
  x("chmod +x /var/lib/nmap/do_nmap_scan.sh")
  nmapScanConf = scOpen("/var/lib/nmap/do_nmap_scan.sh")
  nmapScanConf.replace("${nmap_targets}",subnet)
  
  
  shutil.copy(app.SYCO_PATH + "var/nmap/nmap_cron",  "/etc/cron.weekly/nmap_cron")
  x("chmod +x /etc/cron.weekly/nmap_cron")
  nmapScanCron = scOpen("/etc/cron.weekly/nmap_cron")
  nmapScanCron.replace("${alert_email}",config.general.get_admin_email())
  
  version_obj.mark_executed()
  do_inital_nmap_scan(args)

def uninstall_nmap(args):
  '''
  Uninstall nmap

  '''
  
  x("yum -y remove nmap")
  x("rm /var/lib/nmap/do_nmap_scan.sh")
  x("rm /etc/cron.weekly/nmap_cron")
  


  version_obj = version.Version("InstallNMAP", SCRIPT_VERSION)
  version_obj.mark_uninstalled()

def do_inital_nmap_scan(args):
  app.print_verbose("Doing initial NMAP scanning")
  subnet = config.general.get_subnet()
  if not subnet:
    raise('Need to put network.subnet in install.cfg')

  
  x("/usr/bin/env nmap -v -T4 -F -sV -oX /var/lib/nmap/initial_nmap.xml %s" % subnet)
  #x("/usr/bin/env nmap %s > /tmp/initial_scan.txt" % subnet)