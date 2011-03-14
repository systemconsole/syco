#!/usr/bin/env python
'''
Install LDAP client and server.

Read more:
http://wiki.centos.org/HowTos/DirectoryServerSetup
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/pdf/Installation_Guide/Red_Hat_Directory_Server-8.2-Installation_Guide-en-US.pdf
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/html/Administration_Guide/index.html
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/html/Administration_Guide/User_Account_Management.html
http://www.oreillynet.com/sysadmin/blog/2006/07/a_new_favorite_fedora_director.html

LDAP Read
http://www.linux.com/archive/feature/114074
http://www.howtoforge.com/linux_ldap_authentication
http://www.debuntu.org/ldap-server-and-linux-ldap-clients
http://www.yolinux.com/TUTORIALS/LDAP_Authentication.html

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import app, general, version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-ldap-server", install_ldap_server, help="Install ldap server.")
  commands.add("install-ldap-client", install_ldap_client, help="Install ldap client.")  
  commands.add("uninstall-ldap",      uninstall_ldap, help="Uninstall ldap client/server.")  

def install_ldap_server(self):
  '''
  Install ldap server on current host.

  '''
  app.print_verbose("Install ldap server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.check_executed()
  
  # LDAP port 389
  # LDAPS port 636
  # Admin port 9830
  
  # Prepare Centos Directory Servive installation
  echo "search fareonline.net" >> /etc/resolv.conf 
  echo "domain fareonline.net" >> /etc/resolv.conf
  
  yum install centos-ds
  Is this ok [y/N]: y
  
  ??yum install xorg-x11-xauth bitstream-vera-fonts dejavu-lgc-fonts urw-fonts
  
  setup-ds-admin.pl -s -f General.FullMachineName=ldap.fareonline.net /tmp/setupodCboP.inf RootDNPwd=xx ConfigDirectoryAdminPwd=xx ServerAdminPwd=xx 

  if "cat /proc/sys/fs/file-ma" < 64000
    echo "fs.file-max = 64000" >>  /etc/sysctl.con
    
  echo "*        -        nofile        8192" >>  /etc/security/limits.conf  
  echo "session required /lib/security/$ISA/pam_limits.so" >>  /etc/pam.d/system-aut
  
  /usr/bin/centos-idm-console -a http://localhost:9830
 
  
  version_obj.mark_executed()  


def install_ldap_client(self):
  '''
  Install ldap client on current host and connect to networks ldap server.

  '''
  app.print_verbose("Install ldap server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.check_executed()
  
  version_obj.mark_executed()
  

def uninstall_ldap(self):
  '''
  Uninstall both ldap client and server.

  '''
  app.print_verbose("Uninstall ldap client/server")
  /usr/sbin/ds_removal -s ldap -w PASSWORD
  service dirsrv-admin stop
  
  

  
  yum erase  centos-ds adminutil alsa-lib antlr apr apr-util centos-admin-console centos-ds-admin centos-ds-base centos-ds-console centos-idm-console cyrus-sasl-gssapi cyrus-sasl-md5 db4-utils giflib gjdoc httpd idm-console-framework java-1.4.2-gcj-compat java-1.6.0-openjdk jpackage-utils jss ldapjdk libXtst libart_lgpl libgcj libicu lm_sensors mod_nss mozldap mozldap-tools net-snmp-libs perl-Mozilla-LDAP postgresql-libs svrcore tzdata-java 