#!/usr/bin/env python
'''
Install FreeRadius.

Read more
www.freeradius.org

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
  commands.add("install-radius",             install_freeradius, help="Install FreeRadius server on the current server.")
  commands.add("uninstall-radius",           uninstall_freeradius,           help="Uninstall Freeradius server on the current server.")
  

def install_freeradius(args):
  '''
  Install and configure the mysql-server on the local host.

  '''
  app.print_verbose("Install FreeRadius version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallFreeRadius", SCRIPT_VERSION)
  version_obj.check_executed()

 


  # Install the mysql-server packages.
  if (not os.access("/usr/sbin/radiusd", os.W_OK|os.X_OK)):
    x("yum -y install freeradius-utils freeradius-ldap")

    x("/sbin/chkconfig radiusd on ")
    if (not os.access("/usr/sbin/radiusd", os.F_OK)):
      raise Exception("Couldn't install FreeRadius")

  # Configure iptables
  iptables.add_freeradius_chain()
  iptables.save()
  
  app.print_verbose("Copying config")
  
  ldapconf = scOpen("/etc/raddb/modules/ldap")
  ldapconf.replace("\\t*server =.*","\\tserver=\"ldaps://%s\"" % config.general.get_ldap_hostname())
  ldapconf.replace("\\t#password = .*","\\tpassword =%s" % app.get_ldap_admin_password())
  ldapconf.replace("\\t#identity = .*","\\tidentity = \"cn=Manager,%s\"" % config.general.get_ldap_dn())
  ldapconf.replace("\\t#base_filter = .*","\\tbase_filter = \"(employeeType=Sysop)\"")
  ldapconf.replace("\\tfilter = .*", "\\tfilter =\"(uid=%u)\"")
  ldapconf.replace("\\tbasedn = .*", "\\tbasedn =\"%s\"" % config.general.get_ldap_dn())
  
  #Deal with certs
  ldapconf.replace("\\t\\t# cacertfile.*=.*","\\t\\tcacertfile\\t= /etc/openldap/cacerts/ca.crt")
  ldapconf.replace("\\t\\t# certfile.*=.*","\\t\\tcertfile\\t= /etc/openldap/cacerts/client.crt")
  ldapconf.replace("\\t\\t# keyfile.*=.*","\\t\\tkeyfile\\t= /etc/openldap/cacerts/client.key")
  
  

  x("/usr/bin/awk '/^[#]\\tldap/{c++;if(c==1){sub(\"^[#]\\tldap\",\"\\tldap\")}}1' %s" % "/etc/raddb/sites-enabled/default > /etc/raddb/sites-enabled/default.tmp")
  x("cp /etc/raddb/sites-enabled/default.tmp /etc/raddb/sites-enabled/default")
  x("rm /etc/raddb/sites-enabled/default.tmp")
  version_obj.mark_executed()

def uninstall_freeradius(args):
  '''
  Uninstall freeradius

  '''
  if (os.access("/etc/init.d/radiusd", os.F_OK)):
    x("/etc/init.d/radiusd stop")
  x("yum -y remove freeradius")
  
  x("rm -rf /etc/raddb")


  version_obj = version.Version("InstallFreeRadius", SCRIPT_VERSION)
  version_obj.mark_uninstalled()
