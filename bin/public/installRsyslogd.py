#!/usr/bin/env python
'''
Install of rsyslog server with mysql backend

Install rsyslog server and set up tls server on tcp port 514 and unecrypted
logning on udp 514.

NOTE: Client certs need to be regenerated once year.

LOGGING TO
Logs are saved to an mysql database Syslog. And to files structure in
/var/log/remote/year/month/day/servername

NEW CERTS
$ syco install-rsyslogd-newcerts
Installation can generate certs for rsyslog client. Certs are stored in
/etc/pki/rsyslog folder.

Clients can then get their certs from that location.

CONFIG FILES
rsyslog.d config files are located in syco/var/rsyslog/ folder. Template used
for generating certs are located in /syco/var/rsyslog/template.ca and
template.server

READING
http://www.rsyslog.com/doc/rsyslog_tls.html
http://www.rsyslog.com/doc/rsyslog_mysql.html

'''

__author__ = "matte@elino.se, daniel@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

from config import get_servers
from general import generate_password, get_install_dir
from general import x
from installMysql import install_mysql, mysql_exec
from scopen import scOpen
import app
import config
import general
import mysqlUtils
import net
import version


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-rsyslogd",          install_rsyslogd,   help="Install Rsyslog server.")
    commands.add("uninstall-rsyslogd",        uninstall_rsyslogd, help="Uninstall rsyslog server and all certs on the server.")
    commands.add("install-rsyslogd-newcerts", rsyslog_newcerts,   help="Generats new cert for rsyslogd clients.")


def install_rsyslogd(args):
    '''
    Install rsyslogd on the server.

    '''
    app.print_verbose("Install rsyslogd.")
    version_obj = version.Version("InstallRsyslogd", SCRIPT_VERSION)
    version_obj.check_executed()

    # Initialize all passwords used by the script
    app.init_mysql_passwords()

    # Setup syco dependencies.
    if not os.path.exists('/etc/init.d/mysqld'):
        install_mysql(["","1","1G"])

    # Installing packages
    if not os.path.exists('/etc/init.d/rsyslog'):
        x("yum install rsyslog rsyslog-gnutls rsyslog-mysql gnutls-utils -y")

    # Autostart rsyslog at boot
    x("chkconfig rsyslog on")

    # Generation new certs if no certs exsists
    if not os.path.exists('/etc/pki/rsyslog/ca.crt'):
        rsyslog_newcerts(args)

    sql_password = generate_password(20)
    _setup_database(sql_password)
    _setup_rsyslogd(sql_password)

    # Restarting service
    x("/etc/init.d/rsyslog restart")
    version_obj.mark_executed()


def _setup_database(sql_password):
    '''
    Configure database for rsyslog

    '''
    mysqlUtils.drop_user('rsyslogd')
    mysqlUtils.create_user('rsyslogd', sql_password, 'syslog')

    mysql_exec("\. {0}rsyslog/initdb.sql".format(app.SYCO_VAR_PATH), 'root')


def _setup_rsyslogd(sql_password):
    '''
    Setup rsyslogd config files.

    '''
    x("cp -f /opt/syco/var/rsyslog/rsyslogd.conf /etc/rsyslog.conf")
    sc = scOpen("/etc/rsyslog.conf")
    sc.replace('${SQLPASSWORD}', sql_password)
    sc.replace('${SERVERNAME}', '{0}.{1}'.format(
        net.get_hostname(), config.general.get_resolv_domain())
    )
    sc.replace('${DOMAIN}', config.general.get_resolv_domain())

    # Setup folder to store logs from clients.
    x("mkdir /var/log/remote")
    x("restorecon /var/log/remote")


def rsyslog_newcerts(args):
    '''
    Generate new tls certs for rsyslog server and all clients defined in install.cfg.

    NOTE: This needs to be executed once a year.

    '''
    x("mkdir -p /etc/pki/rsyslog")

    # Copy certs template
    template_ca = "{0}template.ca".format(get_install_dir())
    x("cp -f /opt/syco/var/rsyslog/template.ca {0}".format(template_ca))

    hostname = "{0}.{1}".format(net.get_hostname(), config.general.get_resolv_domain())
    _replace_tags(template_ca, hostname)

    # Making CA
    x("certtool --generate-privkey --outfile /etc/pki/rsyslog/ca.key")
    x("certtool --generate-self-signed --load-privkey /etc/pki/rsyslog/ca.key "+
      "--outfile /etc/pki/rsyslog/ca.crt " +
      "--template {0}".format(template_ca)
    )

    #
    # Create rsyslog SERVER cert
    #
    for server in get_servers():
        _create_cert(server)


def _create_cert(hostname):
    '''
    Create certificate for one rsyslog client.

    '''
    fqdn = "{0}.{1}".format(hostname, config.general.get_resolv_domain())
    app.print_verbose("Create cert for host: {0}".format(fqdn))

    template_server = "{0}template.{1}".format(get_install_dir(), fqdn)
    x("cp -f /opt/syco/var/rsyslog/template.server {0}".format(template_server))
    _replace_tags(template_server, fqdn)

    # Create key
    x("certtool --generate-privkey " +
      "--outfile /etc/pki/rsyslog/{0}.key".format(fqdn)
    )

    # Create cert
    x("certtool --generate-request " +
      "--load-privkey /etc/pki/rsyslog/{0}.key ".format(fqdn) +
      "--outfile /etc/pki/rsyslog/{0}.csr ".format(fqdn) +
      "--template {0}".format(template_server)
    )

    # Sign cert
    x("certtool --generate-certificate " +
      "--load-request /etc/pki/rsyslog/{0}.csr ".format(fqdn) +
      "--outfile /etc/pki/rsyslog/{0}.crt ".format(fqdn) +
      "--load-ca-certificate /etc/pki/rsyslog/ca.crt " +
      "--load-ca-privkey /etc/pki/rsyslog/ca.key " +
      "--template {0}".format(template_server)
    )


def _replace_tags(filename, fqdn):
    '''
    Replace all tags in template files with apropriate values.

    '''
    sc = scOpen(filename)
    sc.replace('${ORGANIZATION}', config.general.get_organization_name())
    sc.replace('${UNIT}', config.general.get_organizational_unit_name())
    sc.replace('${LOCALITY}', config.general.get_locality())
    sc.replace('${STATE}', config.general.get_state())
    sc.replace('${COUNTRY}', config.general.get_country_name())
    sc.replace('${CN}', fqdn)
    sc.replace('${DNS_NAME}', fqdn)
    sc.replace('${EMAIL}', config.general.get_admin_email())
    sc.replace('${SERIAL}', _get_serial())


def _get_serial():
    '''
    Return a unique (autoinc) serial number that are used in template files.

    '''
    _get_serial.serial = _get_serial.serial + 1
    return str(_get_serial.serial)
_get_serial.serial = 0


def uninstall_rsyslogd(args):
    '''
    Remove Rsyslogd server from the server

    '''
    app.print_verbose("Uninstall Rsyslogd SERVER")
    x("yum erase rsyslog rsyslog-gnutls rsyslog-mysql gnutls-utils")
    x("rm -rf /etc/pki/rsyslog")
