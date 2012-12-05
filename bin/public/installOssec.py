#!/usr/bin/env python
'''
Install of OSSEC AGENT / CLIENT

See installOssecd for more info.

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


from general import x
from general import x, download_file, md5checksum, get_install_dir
from installOssecd import build_ossec
from scopen import scOpen
from ssh import scp_from
import app
import config
import general
import install
import iptables
import socket
import time
import version


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-ossec-client",   install_ossec_client,   help="Install Ossec Client.")
    commands.add("uninstall-ossec-client", uninstall_ossec_client, help="uninstall Ossec Client.")


def install_ossec_client(args):
    '''
    Install OSSEC Client on the server

    '''

    if os.path.exists('/var/ossec/bin/manage_agents'):
        app.print_error("Not insalling OSSEC client since OSSEC server detected")
        return

    app.print_verbose("Install ossec client.")
    version_obj = version.Version("InstallOssec", SCRIPT_VERSION)
    version_obj.check_executed()

    # Initialize all passwords used by the script
    app.init_mysql_passwords()

    build_ossec('preloaded-vars-client.conf')
    _setup_conf()
    _setup_keys()

    # Enabling syslog logging
    x('/var/ossec/bin/ossec-control enable client-syslog')

    # Adding iptables rules
    iptables.add_ossec_chain()
    iptables.save()

    # Restaring OSSEC server
    x("service ossec restart")

    x('yum remove gcc make perl-Time-HiRes -y')

    version_obj.mark_executed()


def _setup_conf():
    '''
    Setup ossec.conf for client/agent.

    '''
    x('rm -f /var/ossec/etc/ossec.conf')
    x('cp -f /opt/syco/var/ossec/ossec_agent.conf /var/ossec/etc/ossec.conf')
    x('chown root:ossec /var/ossec/etc/ossec.conf')
    x('chmod 640 /var/ossec/etc/ossec.conf')

    conf = scOpen("/var/ossec/etc/ossec.conf")
    conf.replace("${OSSECSERVER}", config.general.get_ossec_server_ip())


def _setup_keys():
    '''
    Download client keys from server.

    Needed for client to be allowed to communicate with server.

    '''
    ossecserver = config.general.get_ossec_server_ip()
    hostname = socket.gethostname()
    fqdn = '{0}.{1}'.format(hostname, config.general.get_resolv_domain())

    # Wait until ssh is responsive on server. However this doesn't mean that
    # the server is fully installed.
    general.wait_for_server_to_start(ossecserver, 22)

    # Loop until ossec server has created client keys and made it possible
    # to copy them.
    while True:
        scp_from(
            ossecserver,
            "/var/ossec/etc/{0}_client.keys".format(fqdn),
            "/var/ossec/etc/client.keys"
        )

        # Loop until the keys are downloaded.
        if os.path.exists('/var/ossec/etc/client.keys'):
            break

        # Wait awhile and then try to download the files again.
        time.sleep(40)

    x('chown root:ossec /var/ossec/etc/client.keys')
    x('chmod 640 /var/ossec/etc/client.keys')


def uninstall_ossec_client(args):
  '''
  Remove OSSECD Client from the server
  @todo: Will uninstall the server aswell.

  '''
  if os.path.exists('/var/ossec/bin/manage_agents'):
    app.print_error("Not uninsalling OSSEC client since OSSEC server detected")
    return

  # Stoping OSSEC client
  x('/var/ossec/bin/ossec-control stop')

  # Remove folders
  x('rm -rf /var/ossec')
