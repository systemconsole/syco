#!/usr/bin/env python
'''
Install rsyslog client tghat connect to a rsyslogd server.

The connection will be done through tls on port 514 and unencrypted on udp 514.

LOGING TO
Logs are the saved local on server, and then sent to rsyslogd server to
store in structure /var/log/remote/year/month/day/servername and mysql server.

NEW CERTS
Clients will copy their certs from the rsyslog server.

CONFIG FILES
rsyslog.d config files are located in syco/var/rsyslog/ folder

SEE
installRsyslogd.py for more info.

'''

__author__ = "daniel@cybercow.se, matte@elino.se, "
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import os
import socket

from config import get_servers, host
from general import x
from scopen import scOpen
from ssh import scp_from
import app
import config
import general
import installLogrotate
import installRsyslogd
import iptables
import net
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-rsyslogd-client", install_rsyslogd_client, help="Install rsyslog client on the server.")
    commands.add("uninstall-rsyslogd-client", uninstall_rsyslogd_client, help="uninstall rsyslog client and all certs from the server.")


def install_rsyslogd_client(args):
    '''
    Install rsyslog client the server

    '''
    app.print_verbose("Install rsyslog client.")

    # If rsyslogd is installed, raise exception.
    version_obj = version.Version("InstallRsyslogd", installRsyslogd.SCRIPT_VERSION)
    version_obj.check_executed()

    #
    version_obj = version.Version("InstallRsyslogdClient", SCRIPT_VERSION)
    version_obj.check_executed()

    # Initialize all passwords used by the script
    app.init_mysql_passwords()

    #Enabling iptables before server has start
    iptables.add_rsyslog_chain("client")
    iptables.save()

    # Wating for rsyslog Server to start
    general.wait_for_server_to_start(config.general.get_log_server_hostname1(), "514")

    app.print_verbose("CIS 5.2 Configure rsyslog")

    app.print_verbose("CIS 5.2.1 Install the rsyslog package")
    x("yum install rsyslog rsyslog-gnutls -y")

    app.print_verbose("CIS 5.2.2 Activate the rsyslog Service")
    if os.path.exists('/etc/xinetd.d/syslog'):
        x("chkconfig syslog off")
    x("chkconfig rsyslog on")

    _configure_rsyslog_conf()
    _copy_cert()

    # Restaring rsyslog
    x("/etc/init.d/rsyslog restart")

    # Configure logrotate
    installLogrotate.install_logrotate(args)

    version_obj.mark_executed()


def _configure_rsyslog_conf():
    '''
    Create/configure the rsyslog.conf file.

    '''
    app.print_verbose("CIS 5.2.3 Configure /etc/rsyslog.conf")
    x("cp -f /opt/syco/var/rsyslog/rsyslog.conf /etc/rsyslog.conf")
    _replace_tags()
    x("chmod 640 /etc/rsyslog.conf")


def _replace_tags():
    '''
    Replace all tags in template files with apropriate values.

    '''
    sc = scOpen("/etc/rsyslog.conf")
    sc.replace('${MASTER}', config.general.get_log_server_hostname1())
    sc.replace('${SLAVE}',  config.general.get_log_server_hostname2())
    sc.replace('${DOMAIN}', config.general.get_resolv_domain())

    fqdn = "{0}.{1}".format(net.get_hostname(), config.general.get_resolv_domain())
    sc.replace('${SERVERNAME}', fqdn)


def _copy_cert():
    '''
    Coping certs for tls from rsyslog server

    '''
    crt_dir ="/etc/pki/rsyslog"
    x("mkdir -p {0}".format(crt_dir))
    srv = config.general.get_log_server_hostname1()
    scp_from(srv, "/etc/pki/rsyslog/{0}*".format(net.get_hostname()), crt_dir)
    scp_from(srv, "/etc/pki/rsyslog/ca.crt", crt_dir)
    x("restorecon -r /etc/pki/rsyslog")
    x("chmod 600 /etc/pki/rsyslog/*")
    x("chown root:root /etc/pki/rsyslog/*")


def uninstall_rsyslogd_client(args):
    '''
    Unistall rsyslog and erase all files
    '''
    x("yum erase rsyslog -y")
    x("rm -rf /etc/pki/rsyslog")
    version_obj = version.Version("InstallRsyslogdClient", SCRIPT_VERSION)
    version_obj.mark_uninstalled()
