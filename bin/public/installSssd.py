#!/usr/bin/env python
'''
Install sssd that will connect to an LDAP-server.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "2.0.0"
__status__ = "Production"

import os
import re

import app
import config
import general
from general import shell_exec
from general import shell_run
import iptables
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 2

LDAP_SERVER_HOST_NAME = config.general.get_ldap_hostname()
LDAP_DN = config.general.get_ldap_dn()

def build_commands(commands):
  commands.add("install-sssd", install_sssd, help="Install sssd (ldap client).")
  commands.add("uninstall-sssd", uninstall_sssd, help="Uninstall sssd.")

def install_sssd(args):
  '''
  Install ldap client on current host and connect to networks ldap server.

  '''

  #http://serverfault.com/questions/299855/centos-6-linux-and-nss-pam-ldapd


  app.print_verbose("Install ldap server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.check_executed()

  install.package("authconfig")
  install.package("pam_ldap")
  install.package("nscd")
  iptables.add_ldap_chain()
  iptables.save()

  ip = config.general.get_ldap_server_ip()
  general.wait_for_server_to_start(ip, "389")

  # Copy the TLS cert needed to login to the ldap-server.
  shell_run("scp root@" + ip + ":/etc/openldap/cacerts/ldap.pem /etc/openldap/cacerts/ldap.pem",
    events={
      'Are you sure you want to continue connecting \(yes\/no\)\?': "YES\n",
      "root@" + ip + "\'s password\:": app.get_root_password() + "\n"
    }
  )

  shell_run("scp root@" + ip + ":/etc/openldap/cacerts/ca.cert /etc/openldap/cacerts/ca.cert",
    events={
      'Are you sure you want to continue connecting \(yes\/no\)\?': "YES\n",
      "root@" + ip + "\'s password\:": app.get_root_password() + "\n"
    }
  )

  shell_exec("/usr/sbin/cacertdir_rehash /etc/openldap/cacerts")

  # Enable as a client
  shell_exec("authconfig --enableldap --enableldaptls --enableldapauth --disablenis --enablecache --enablemkhomedir --enablelocauthorize " +
    "--ldapserver=" + LDAP_SERVER_HOST_NAME + " --ldapbasedn=" + LDAP_DN + " "
    "--updateall")

  version_obj.mark_executed()

def uninstall_sssd(args):
    pass
