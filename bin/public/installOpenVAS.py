#!/usr/bin/env python
'''
Install OpenVAS.

Read more
http://openvas.org
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
  commands.add("install-openvas",             install_openvas, help="Install OpenVAS.")
  commands.add("uninstall-openvas",           uninstall_openvas,           help="Uninstall NMAP.")



def install_openvas(args):
  '''
  Install and configure openvas on the local host.

  '''
  app.print_verbose("Install OpenVAS version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallOpenVAS", SCRIPT_VERSION)
  version_obj.check_executed()

 
  ##app.print_verbose("Adding atomic repo for yum...")
  #x("wget -q -O - http://www.atomicorp.com/installers/atomic | sh")
  
  
  if (not os.access("/etc/yum.repos.d/atomic.repo", os.F_OK)):
    raise Exception("You need to install the atomic repo first (wget -q -O - http://www.atomicorp.com/installers/atomic | sh)")
  # Install the mysql-server packages.
  
  
  subnet = config.general.get_subnet()
  if not subnet:
    raise('Need to put network.subnet in install.cfg')
  x("yum -y install sqlite")
  if (not os.access("/usr/sbin/openvassd", os.W_OK|os.X_OK)):
    x("yum -y install openvas")

    if (not os.access("/usr/sbin/openvassd", os.F_OK)):
      raise Exception("Couldn't install OpenVAS")



  iptables.add_openvas_chain()
  iptables.save()
  
  app.print_verbose("Disabling SELinux")
  x("/usr/sbin/setenforce 0")
  app.print_verbose("Get OpenVAS nvt: %d" % SCRIPT_VERSION)
  x("openvas-nvt-sync --wget &> /dev/null ")
  app.print_verbose("Rebuild OpenVAS database: %d" % SCRIPT_VERSION)
  x("openvasmd --rebuild")
  app.print_verbose("Add default OpenVAS admin user: %d" % SCRIPT_VERSION)
  x("openvasad -c 'add_user' -u admin -w admin  --role=Admin ")
  # Configure iptables
  
  #Need to modify config, and make sure all services are started
  gsadconf = scOpen("/etc/sysconfig/gsad")
  gsadconf.replace("^GSA_ADDRESS=127\.0\.0\.1","GSA_ADDRESS=0\.0\.0\.0")
  gsadconf.replace("^#GSA_SSL_PRIVATE_KEY=","GSA_SSL_PRIVATE_KEY=/var/lib/openvas/private/CA/serverkey.pem")
  gsadconf.replace("^#GSA_SSL_CERTIFICATE=","GSA_SSL_CERTIFICATE=/var/lib/openvas/CA/servercert.pem")

  # Disable SELINUX it just messes with me.
  app.print_verbose("Disabling SELINUX")
  x("echo 0 > /selinux/enforce")
  selinuxconf = scOpen("/etc/selinux/config")
  selinuxconf.replace("^SELINUX=.*","SELINUX=permissive")

  #Setup default database
  shutil.copy(app.SYCO_PATH + "var/openvas/sql_init.sql",  app.SYCO_PATH + "var/openvas/sql_init.sql.tmp")
  
  sqlInit = scOpen(app.SYCO_PATH + "var/openvas/sql_init.sql.tmp")
  sqlInit.replace("${syco_hosts}",subnet)
  sqlInit.replace("${syco_alert_email}",config.general.get_admin_email())
  x("cat %s/var/openvas/sql_init.sql.tmp | sqlite3 /var/lib/openvas/mgr/tasks.db" % app.SYCO_PATH )
  
  #general.shell_exec("/etc/init.d/openvas-manager restart &> /dev/null ")
  #general.shell_exec("/etc/init.d/openvas-administrator restart &> /dev/null")
  #general.shell_exec("/etc/init.d/openvas-scanner restart &> /dev/null")
  #general.shell_exec("/etc/init.d/gsad restart &> /dev/null")
  #general.shell_exec("service gsad start")
  x("/bin/sh "+app.SYCO_PATH + "var/openvas/restart.sh &> /dev/null ")
  
  version_obj.mark_executed()

def uninstall_openvas(args):
  '''
  Uninstall nmap

  '''
  
  if (os.access("/etc/init.d/openvas-manager", os.F_OK)):
    general.shell_exec("/etc/init.d/openvas-manager stop")
    general.shell_exec("/etc/init.d/openvas-scanner stop")
    general.shell_exec("/etc/init.d/gsad stop")



  x("yum -y remove openvas-*")
  x("rm -rf /var/lib/openvas")
  #x("rm /etc/yum.repos.d/atomic.repo")
  iptables.del_openvas_chain()
  iptables.save()
  app.print_verbose("Enabling SELINUX")
  x("echo 1 > /selinux/enforce")
  selinuxconf = scOpen("/etc/selinux/config")
  selinuxconf.replace("^SELINUX=.*","SELINUX=enforcing")

  version_obj = version.Version("InstallOpenVAS", SCRIPT_VERSION)
  version_obj.mark_uninstalled()
