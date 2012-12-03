#!/usr/bin/env python
'''
Install the server to act as a openvpn server

Will use x.x.x.0:1194 as the vpn client net taken from log.network in cfg file.

More info about openvpn.
http://openvpn.net/index.php/open-source/documentation/howto.html
http://notes.brooks.nu/2008/08/openvpn-setup-on-centos-52/
http://www.howtoforge.com/openvpn-server-on-centos-5.2
http://www.throx.net/2008/04/13/openvpn-and-centos-5-installation-and-configuration-guide/

TODO: yum installopenvpn-auth-ldap ??

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
import stat

from general import x
from scopen import scOpen
import app
import config
import general
import install
import iptables
import net
import version


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-openvpn-server", install_openvpn_server, help="Install openvpn-server on the current server.")
  commands.add("install-openvpn-client-certs", build_client_certs, help="Build client certs on the openvpn server.")

def install_openvpn_server(args):
  '''
  The actual installation of openvpn server.

  '''
  app.print_verbose("Install openvpn server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallOpenvpnServer", SCRIPT_VERSION)
  version_obj.check_executed()

  x("yum -y install openvpn openvpn-auth-ldap")

  if (not os.access("/etc/openvpn/easy-rsa", os.F_OK)):
    x("cp -R /usr/share/openvpn/easy-rsa/2.0 /etc/openvpn/easy-rsa")

    # Install server.conf
    serverConf = "/etc/openvpn/server.conf"
    x("cp " + app.SYCO_PATH + "/var/openvpn/server.conf %s" % serverConf)
    scOpen(serverConf).replace('${EXTERN_IP}',  net.get_public_ip())
    scOpen(serverConf).replace('${OPENVPN.NETWORK}',  config.general.get_openvpn_network())
    scOpen(serverConf).replace('${FRONT.NETWORK}',  config.general.get_front_network())
    scOpen(serverConf).replace('${FRONT.NETMASK}',  config.general.get_front_netmask())
    scOpen(serverConf).replace('${BACK.NETWORK}',  config.general.get_back_network())
    scOpen(serverConf).replace('${BACK.NETMASK}',  config.general.get_back_netmask())

    # Prepare the ca cert generation.
    fn = "/etc/openvpn/easy-rsa/vars"
    scOpen(fn).replace('[\s]*export KEY_COUNTRY.*',  'export KEY_COUNTRY="' + config.general.get_country_name() + '"')
    scOpen(fn).replace('[\s]*export KEY_PROVINCE.*', 'export KEY_PROVINCE="' + config.general.get_state() + '"')
    scOpen(fn).replace('[\s]*export KEY_CITY.*',     'export KEY_CITY="' + config.general.get_locality() + '"')
    scOpen(fn).replace('[\s]*export KEY_ORG.*',      'export KEY_ORG="' + config.general.get_organization_name() + '"')
    scOpen(fn).replace('[\s]*export KEY_OU.*',       'export KEY_OU="' + config.general.get_organizational_unit_name() + '"')
    scOpen(fn).replace('[\s]*export KEY_EMAIL.*',    'export KEY_EMAIL="' + config.general.get_admin_email() + '"')

    # Can't find the current version of openssl.cnf.
    scOpen("/etc/openvpn/easy-rsa/whichopensslcnf").replace("\[\[\:alnum\:\]\]", "[[:alnum:]]*")

    # Generate CA cert
    os.chdir("/etc/openvpn/easy-rsa/")
    x(". ./vars;./clean-all;./build-ca --batch;./build-key-server --batch server;./build-dh")
    x("cp /etc/openvpn/easy-rsa/keys/{ca.crt,ca.key,server.crt,server.key,dh1024.pem} /etc/openvpn/")

    # To prevent error "TXT_DB error number 2" when running ./build-key-pkcs12 --batch xxx"
    scOpen("/etc/openvpn/easy-rsa/keys/index.txt.attr").replace("unique_subject.*", "unique_subject = no")

  # To be able to route trafic to internal network
  net.enable_ip_forward()

  _setup_ldap()

  iptables.add_openvpn_chain()
  iptables.save()

  x("/etc/init.d/openvpn restart")
  x("/sbin/chkconfig openvpn on")

  build_client_certs(args)

  version_obj.mark_executed()


def _setup_ldap():
  '''
  Configure openvpn to authenticate through LDAP.

  '''
  ldapconf = scOpen("/etc/openvpn/auth/ldap.conf")
  ldapconf.replace("^\\s*URL\s*.*","\\tURL\\tldaps://%s" % config.general.get_ldap_hostname())
  ldapconf.replace("^\s*# Password\s*.*","\\tPassword\\t%s" % app.get_ldap_admin_password())
  ldapconf.replace("^\s*# BindDN\s*.*","\\tBindDN\\tcn=Manager,%s" % config.general.get_ldap_dn())
  ldapconf.replace("^\s*TLSEnable\s*.*","\\t# TLSEnable\\t YES")

  # Deal with certs
  ldapconf.replace("^\s*TLSCACertFile\s*.*","\\tTLSCACertFile\\t /etc/openldap/cacerts/ca.crt")
  ldapconf.replace("^\s*TLSCACertDir\s*.*","\\tTLSCACertDir\\t /etc/openldap/cacerts/")
  ldapconf.replace("^\s*TLSCertFile\s*.*","\\tTLSCertFile\\t /etc/openldap/cacerts/client.crt")
  ldapconf.replace("^\s*TLSKeyFile\s*.*","\\tTLSKeyFile\\t /etc/openldap/cacerts/client.key")

  # Auth
  ldapconf.replace("^\s*BaseDN\s*.*","\\BaseDN\\t \"%s\"" % config.general.get_ldap_dn() )
  ldapconf.replace("^\s*SearchFilter\s*.*","\\tSearchFilter\\t \"(\\&(uid=%u)(employeeType=Sysop))\"")

  x('echo "plugin /usr/lib64/openvpn/plugin/lib/openvpn-auth-ldap.so /etc/openvpn/auth/ldap.conf" >> /etc/openvpn/server.conf ')


def build_client_certs(args):
  install.package("zip")
  os.chdir("/etc/openvpn/easy-rsa/keys")
  general.set_config_property("/etc/cronjob", "01 * * * * root run-parts syco build_client_certs", "01 * * * * root run-parts syco build_client_certs")

  # Create client.conf
  clientConf = "/etc/openvpn/easy-rsa/keys/client.conf"
  x("cp " + app.SYCO_PATH + "/var/openvpn/client.conf %s" % clientConf)
  scOpen(clientConf).replace('${OPENVPN.HOSTNAME}',  config.general.get_openvpn_hostname())

  x("cp " + app.SYCO_PATH + "/doc/openvpn/install.txt .")

  for user in os.listdir("/home"):
    cert_already_installed=os.access("/home/" + user +"/openvpn_client_keys.zip", os.F_OK)
    valid_file="lost+found" not in user
    if valid_file and not cert_already_installed:
      os.chdir("/etc/openvpn/easy-rsa/")
      general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_CN.*',    'export KEY_CN="' + user + '"')
      general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_NAME.*',  'export KEY_NAME="' + user + '"')

      general.set_config_property("/etc/openvpn/easy-rsa/build-key-pkcs12", '.*export EASY_RSA.*', 'source ./vars;export EASY_RSA="${EASY_RSA:-.}"')

      out = general.shell_exec("./build-key-pkcs12 --batch " + user,
        cwd="/etc/openvpn/easy-rsa/",
        events={'(?i)Enter Export Password:':'\n', '(?i)Verifying - Enter Export Password:':'\n'}
      )
      app.print_verbose(out)

      # Config client.crt
      general.set_config_property("/etc/openvpn/easy-rsa/keys/client.conf", "^cert.*crt", "cert " + user + ".crt")
      general.set_config_property("/etc/openvpn/easy-rsa/keys/client.conf", "^key.*key", "key " + user + ".key")
      general.set_config_property(
        "/etc/openvpn/easy-rsa/keys/client.conf", "${OPENVPN.HOSTNAME}",
        config.general.get_openvpn_hostname()
      )

      os.chdir("/etc/openvpn/easy-rsa/keys")
      x("zip /home/" + user +"/openvpn_client_keys.zip ca.crt " + user + ".crt " + user + ".key " + user + ".p12 client.conf install.txt")
      # Set permission for the user who now owns the file.
      os.chmod("/home/" + user +"/openvpn_client_keys.zip", stat.S_IRUSR | stat.S_IRGRP)
      general.shell_exec("chown " + user + ":users /home/" + user +"/openvpn_client_keys.zip ")
