#!/usr/bin/env python
'''
Install of OSSEC AGENT / CLIENT

Ossec is an host based intrusion detection system. It monitors system logs,
changes made to the system like file changes, and triggers alert to log messages.

The OSSEC AGENT are installed on an client-server and then connects to the
OSSEC Server. OSSEC AGENT fetchs keys from the OSSEC SERVER to be able to
connect to the server.

*IMPORTANT*
The hostname of the client MUST BE THE same as in the install.cfg.
Server called "webbserver" in install.cfg must have hostname
webbserver.domain.se as hostname

LOCATION
OSSEC are installed in /var/ossec folders.

SERVER
To make changes to the OSSEC server edit the file

syco/var/ossec/ossec_agent.conf

SETUP CUSTOM RULES
To make changes and add custom rules edit the file

syco/var/ossec/local_rules.xml


MORE READING
http://www.ossec.net/

'''


__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import shutil
import stat
import sys
import time
import traceback
import config
import iptables
from config import get_servers, host
import app
from general import x, download_file, md5checksum, get_install_dir
import version


# OSSEC DOWNLOAD URL
OSSEC_DOWNLOAD = "http://www.ossec.net/files/ossec-hids-2.8.1.tar.gz"
OSSEC_MD5 = 'c2ffd25180f760e366ab16eeb82ae382'

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1



def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-ossec-server",   install_ossec_server,    help="Install Ossec Server on the server.")
    commands.add("uninstall-ossec-server", uninstall_ossec_server, help="Uninstall Ossec Server and all certs from the server.")


def install_ossec_server(args):
    '''
    Install OSSEC server on the server

    '''
    app.print_verbose("Install ossecd.")
    version_obj = version.Version("InstallOssecd", SCRIPT_VERSION)
    version_obj.check_executed()
    install_dir = get_install_dir()
    build_ossec("preloaded-vars-server.conf")
    _generate_client_keys()

    # Setup server config and local rules from syco
    x('\cp -f /opt/syco/var/ossec/ossec_server.conf /var/ossec/etc/ossec.conf')
    x('chown root:ossec /var/ossec/etc/ossec.conf')
    x('chmod 640 /var/ossec/etc/ossec.conf')

    # Configure rules
    x('cp -f /opt/syco/var/ossec/local_rules.xml /var/ossec/rules/local_rules.xml')
    #x("find /var/ossec/rules -type d -print0 | xargs -0 chmod 750")
    #x("find /var/ossec/rules -type f -print0 | xargs -0 chmod 640")
    x('chown root:ossec /var/ossec/rules/local_rules.xml')
    x('chmod 640  /var/ossec/rules/local_rules.xml')

    # Enabling syslog logging
    x('/var/ossec/bin/ossec-control enable client-syslog')

    # Adding iptables rules
    iptables.add_ossec_chain()
    iptables.save()

    x("service ossec restart")

    # Clean up install
    x('yum remove gcc make perl-Time-HiRes -y')


    version_obj.mark_executed()


def build_ossec(preloaded_conf):
    x('yum install gcc make perl-Time-HiRes -y')

    # Downloading and md5 checking
    download_file(OSSEC_DOWNLOAD, "ossec-hids.tar.gz",md5=OSSEC_MD5)

    # Preparing OSSEC for building
    install_dir = get_install_dir()
    x("tar -C {0} -zxf {0}ossec-hids.tar.gz".format(install_dir))
    x("mv {0}ossec-hids-* {0}ossecbuild".format(install_dir))

    # Coping in ossec settings before build
    x('\cp -f /opt/syco/var/ossec/osseconf/{0} {1}ossecbuild/etc/preloaded-vars.conf'.format(preloaded_conf, install_dir))

    # Building OSSEC
    x('{0}ossecbuild/install.sh'.format(install_dir))

    # Autostart ossec.
    x("chkconfig ossec on")


def _generate_client_keys():
    '''
    Generating keys for all ossec clients.

    And prepare separate key files that can be downloaded by each client.

    '''
    install_dir = get_install_dir()
    for server in get_servers():
        fqdn = '{0}'.format(server)
        fqdn2 = '{0}.{1}'.format(server, config.general.get_resolv_domain())
        x("{0}ossecbuild/contrib/ossec-batch-manager.pl -a --name {1} --ip {2}".format(
        install_dir, fqdn, config.host(server).get_front_ip())
        )

        # Prepare separate key files that can be downloaded by each client.
        x(
            "grep {0} /var/ossec/etc/client.keys > ".format(fqdn) +
            "/var/ossec/etc/{0}_client.keys".format(fqdn2)
        )
    x('chmod 640 /var/ossec/etc/*.keys')
    x('chown ossec:ossec  /var/ossec/etc/*.keys')


def uninstall_ossec_server(args):
    '''
    Remove OSSECD server from the server

    '''
    # Stop OSSEC
    x('/var/ossec/bin/ossec-control stop')
    x('/var/ossec/bin/ossec-remoted stop')

    # Removning folders
    x('rm -rf /var/ossec')
