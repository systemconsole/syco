#!/usr/bin/env python
'''
Install LDAP client and server.

# LDAP Setup
http://www.skills-1st.co.uk/papers/security-with-ldap-jan-2002/security-with-ldap.html
http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/5/html/Deployment_Guide/ch-ldap.html
http://www.openldap.org/doc/admin24/OpenLDAP-Admin-Guide.pdf

# Password policy
http://www.zytrax.com/books/ldap/ch6/ppolicy.html
http://www.openldap.org/software/man.cgi?query=slapo-ppolicy&apropos=0&sektion=5&manpath=OpenLDAP+2.3-Release&format=html

# Enable sudo with LDAP
http://electromech.info/sudo-ldap-with-rhds-linux-open-source.html

# Enable ldap on clients
http://directory.fedoraproject.org/wiki/Howto:PAM

#LDAP Read
http://www.linux.com/archive/feature/114074
http://www.howtoforge.com/linux_ldap_authentication
http://www.debuntu.org/ldap-server-and-linux-ldap-clients
http://www.yolinux.com/TUTORIALS/LDAP_Authentication.html

# 2-factor auth
http://www.wikidsystems.com/
http://www.wikidsystems.com/support/wikid-support-center/how-to/how-to-add-two-factor-authentication-to-openldap-and-freeradius
http://freeradius.org/

# Redhat Directory service.
I tried to used the centos directory service/389 directory service first. But
it feelt to heavy and bloated. And impossible to find documentation about
how to setup the PAM -> ldap. I did choose to use the less complicated openldap.
http://wiki.centos.org/HowTos/DirectoryServerSetup
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/pdf/Installation_Guide/Red_Hat_Directory_Server-8.2-Installation_Guide-en-US.pdf
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/html/Administration_Guide/index.html
http://docs.redhat.com/docs/en-US/Red_Hat_Directory_Server/8.2/html/Administration_Guide/User_Account_Management.html
http://www.oreillynet.com/sysadmin/blog/2006/07/a_new_favorite_fedora_director.html
http://www.linux.com/archive/feature/114074

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import re
import os

import app
import general
import version
from general import shell_exec, shell_run
from iptables import iptables, iptables_save

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

SLAPD_FN = "/etc/openldap/slapd.conf"
LDAP_SERVER_HOST_NAME = app.config.get_ldap_hostname()
LDAP_DN = app.config.get_ldap_dn()

def build_commands(commands):
  commands.add("install-ldap-server", install_ldap_server, help="Install ldap server.")
  commands.add("install-ldap-client", install_ldap_client, help="Install ldap client.")  
  commands.add("uninstall-ldap", uninstall_ldap, help="Uninstall ldap client/server.")  

def install_ldap_server(args):
  '''
  Install ldap server on current host.

  '''
  app.print_verbose("Install ldap server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.check_executed()

  # Get all passwords from user at the start of the script.
  app.get_ca_password()

  # Setup ldap dns/hostname used by slapd  
  value="127.0.0.1 " + LDAP_SERVER_HOST_NAME
  general.set_config_property("/etc/hosts", value, value)

  shell_exec("yum -y install openldap.x86_64 openldap-servers.x86_64 authconfig nss_ldap openldap-servers-overlays.x86_64")

  _setup_slapd_config()  
  #_setup_password_policy()
  _setup_tls()
  _import_users()

  shell_exec("chown -R ldap /var/lib/ldap")
  shell_exec("/etc/init.d/ldap start")
  shell_exec("chkconfig ldap on")  

  _add_iptables_rules()
  iptables_save()

  install_ldap_client(args)

  version_obj.mark_executed()

def install_ldap_client(args):
  '''
  Install ldap client on current host and connect to networks ldap server.

  '''
  app.print_verbose("Install ldap server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.check_executed()

  _add_iptables_rules()
  iptables_save()

  ip = app.config.get_ldap_server_ip()
  general.wait_for_server_to_start(ip, "389")

  # Copy the TLS cert needed to login to the ldap-server.
  #remote_server = ssh.Ssh(app.config.get_ldap_server_ip(), app.get_root_password())
  #remote_server.scp("/etc/openldap/cacerts/ldap.pem", "/etc/openldap/cacerts/ldap.pem")
  shell_run("scp root@" + ip + ":/etc/openldap/cacerts/ldap.pem /etc/openldap/cacerts/ldap.pem",
    events={
      'Are you sure you want to continue connecting \(yes\/no\)\?': "YES\n",
      "root@" + ip + "\'s password\:" : app.get_root_password() + "\n"
    }
  )

  shell_exec("/usr/sbin/cacertdir_rehash /etc/openldap/cacerts")

  # Enable as a client
  shell_exec("authconfig --enableldap --enableldaptls --enableldapauth --disablenis --enablecache " +
    "--ldapserver=" + LDAP_SERVER_HOST_NAME + " --ldapbasedn=" + LDAP_DN + " "
    "--updateall")

  version_obj.mark_executed()

def uninstall_ldap(args):
  '''
  Uninstall both ldap client and server.

  '''
  app.print_verbose("Uninstall ldap client/server")
  shell_exec("yum -y erase openldap-servers openldap-servers-overlays.x86_64")
  shell_exec("rm /etc/openldap/slapd.conf.rpmsave")
  shell_exec("rm -r /var/lib/ldap")
  shell_exec("rm -r /etc/ldap.conf.rpmnew")
  shell_exec("rm -r /etc/ldap.conf.rpmsave")

  _remove_iptables_rules()
  iptables_save()

  version_obj = version.Version("InstallLdapServer", SCRIPT_VERSION)
  version_obj.mark_uninstalled()

def _setup_slapd_config():
  general.set_config_property(SLAPD_FN, ".*suffix.*", 'suffix "' + LDAP_DN + '"')
  general.set_config_property(SLAPD_FN, ".*rootdn.*Manager.*", 'rootdn "cn=Manager,' + LDAP_DN + '"')

  # Not needed for local changes.
  # hash_password = shell_exec('slappasswd -c "%s" -s ' + password)
  # general.set_config_property(SLAPD_FN, ".*rootpw.*[{]crypt[}].*", 'rootpw ' + hash_password)

  # Access Control
  # Users can change their own passwords
  # Everyone can read everything except passwords
  if (not general.grep(SLAPD_FN, "access to attrs=userPassword")):
    f = open(SLAPD_FN, "a")
    f.write("access to attrs=userPassword\n")
    f.write("  by self write\n")
    f.write("  by anonymous auth\n")
    f.write("  by * none\n")
    f.write("access to *\n")
    f.write("  by * read\n")
    f.close()

  # Setup LDAP backend database
  shell_exec("cp /etc/openldap/DB_CONFIG.example /var/lib/ldap/DB_CONFIG")
  shell_exec("slapadd -l " + app.SYCO_PATH + "var/ldap/ldif/common.ldif")

def _setup_password_policy():
  app.print_verbose("Setup password policy.")
  value = "moduleload /usr/lib64/openldap/ppolicy.la"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  value = "include /etc/openldap/schema/ppolicy.schema"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  # Invokes password policies for this DIT only
  value = "overlay ppolicy"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  # Define the default policy
  value = 'ppolicy_default "cn=default,cn=pwpolicies,' + LDAP_DN + '"'
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)  

def _add_iptables_rules():
  '''
  Setup iptables for ldap.

  '''
  app.print_verbose("Setup iptables for nfs")
  _remove_iptables_rules()

  iptables("-N syco_ldap")

  # LDAP non TLS and with TLS
  iptables("-A syco_ldap -m state --state NEW -p tcp --dport 389  -j ACCEPT")

  iptables("-I INPUT  -p ALL -j syco_ldap")
  iptables("-I OUTPUT  -p ALL -j syco_ldap")

def _remove_iptables_rules():
  iptables("-D INPUT  -p ALL -j syco_ldap")
  iptables("-D INPUT  -p ALL -j syco_ldap")
  iptables("-F syco_ldap")
  iptables("-X syco_ldap")  

def _setup_tls():
  '''
  Create TLS cert and setup slapd to use them.
  
  '''
  app.print_verbose("Setup TLS")
  
  # Create dir
  certdir = "/etc/openldap/tls"
  shell_exec("mkdir -p " + certdir)
  
  # Create CA  
  ca_pass_phrase = app.get_ca_password()
  shell_run("openssl genrsa -des3 -out ca.key 2048",
    cwd=certdir,
    events={
      r'Enter pass phrase for ca.key:': ca_pass_phrase + "\n",
      r'Verifying.*Enter pass phrase for ca.key:': ca_pass_phrase + "\n",
    }
  )

  # Create CA cert.
  shell_run("openssl req -new -x509 -days 365 -key ca.key -out ca.cert",
    cwd=certdir,
    events={
      re.compile('Enter pass phrase for ca.key:'): ca_pass_phrase + "\n",
      re.compile('Country Name \(2 letter code\) \[GB\]\:'): app.config.get_country_name() + "\n",
      re.compile('State or Province Name \(full name\) \[Berkshire\]\:'): app.config.get_state() + "\n",
      re.compile('Locality Name \(eg, city\) \[Newbury\]\:'): app.config.get_locality() + "\n",
      re.compile('Organization Name \(eg, company\) \[My Company Ltd\]\:'): app.config.get_organization_name() + "\n",
      re.compile('Organizational Unit Name \(eg, section\) \[\]\:'): app.config.get_organizational_unit_name() + "\n",
      re.compile('Common Name \(eg, your name or your server\'s hostname\) \[\]\:'): app.config.get_organizational_unit_name() + "CA\n",
      re.compile('Email Address \[\]\:'): app.config.get_admin_email() + "\n",
    }
  )
  
  # Create ldap cert
  shell_exec("openssl genrsa -out ldap.key 1024", cwd=certdir)
  shell_run("openssl req -new -key ldap.key -out ldap.csr",
    cwd=certdir,
    events={
      re.compile('Country Name \(2 letter code\) \[GB\]\:'): app.config.get_country_name() + "\n",
      re.compile('State or Province Name \(full name\) \[Berkshire\]\:'): app.config.get_state() + ".\n",
      re.compile('Locality Name \(eg, city\) \[Newbury\]\:'): app.config.get_locality() + ".\n",
      re.compile('Organization Name \(eg, company\) \[My Company Ltd\]\:'): app.config.get_organization_name() + ".\n",
      re.compile('Organizational Unit Name \(eg, section\) \[\]\:'): app.config.get_organizational_unit_name() + "\n",
      re.compile('Common Name \(eg, your name or your server\'s hostname\) \[\]\:'): LDAP_SERVER_HOST_NAME + "\n",
      re.compile('Email Address \[\]\:'): app.config.get_admin_email() + "\n",
      re.compile('A challenge password \[\]\:'): "\n",
      re.compile('An optional company name \[\]\:'): "\n",
    }
  )
  
  # Sign ldap cert with CA.
  shell_run("openssl x509 -req -in ldap.csr -out ldap.cert -CA ca.cert -CAkey ca.key -CAcreateserial -days 365",
    cwd=certdir,
    events={
      r'Enter pass phrase for ca.key:': ca_pass_phrase + "\n",
    }
  )

  shell_exec("cp /etc/openldap/tls/ca.cert /etc/openldap/cacerts/")
  shell_exec("cat /etc/openldap/tls/ldap.key > /etc/openldap/cacerts/ldap.pem")
  shell_exec("cat /etc/openldap/tls/ldap.cert >> /etc/openldap/cacerts/ldap.pem")

  # Configure slapd for TLS
  value = "TLSCertificateFile /etc/openldap/cacerts/ldap.pem"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  value = "TLSCertificateKeyFile /etc/openldap/cacerts/ldap.pem"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  value = "TLSCACertificateFile /etc/openldap/cacerts/ca.cert"
  general.set_config_property(SLAPD_FN, ".*" + value + ".*", value)

  # http://www.openldap.org/doc/admin24/guide.html#Authentication Methods
  value = "security ssf=1 update_ssf=112 simple_bind=64"
  general.set_config_property(SLAPD_FN, ".*" + value +".*", value)

def _import_users():  
  shell_exec("slapadd -l " + app.SYCO_PATH + "var/ldap/ldif/users.ldif")
  shell_exec("slapadd -l " + app.SYCO_PATH + "var/ldap/ldif/groups.ldif")

  for dir in os.listdir(app.SYCO_USR_PATH):
    filename = os.path.abspath(app.SYCO_USR_PATH + dir + "/var/ldap/ldif/users.ldif")
    if (os.access(filename, os.F_OK)):
      shell_exec("slapadd -l " + filename)

    filename = os.path.abspath(app.SYCO_USR_PATH + dir + "/var/ldap/ldif/groups.ldif")
    if (os.access(filename, os.F_OK)):
      shell_exec("slapadd -l " + filename)