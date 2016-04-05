#!/usr/bin/env python
"""
This script will install HA Proxy on the targeted server.

This script is dependent on the following config files for this script to work.
    var/haproxy/[environment].haproxy.conf
"""

__author__ = "David Skeppstedt"
__copyright__ = "Copyright 2014, Fareoffice CRS AB"
__maintainer__ = "David Skeppstedt"
__email__ = "davske@fareoffice.com"
__credits__ = ["Daniel Lindh, Mattias Hemmingsson, Kristoffer Borgstrom"]
__license__ = "???"
__version__ = "1.5"
__status__ = "Production"

import os
from general import x, urlretrive
import ssh
import config
import iptables
import socket
import install
import app
import password
import version
import scopen
import fcntl
import struct
import sys
import re

script_version = 2

cert_server = cert_server_path = cert_copy_to_path = SYCO_PLUGIN_PATH = None


HAPROXY_CONF_DIR = "/etc/haproxy/"
HAPROXY_CONF = "/etc/haproxy/haproxy.cfg"
ACCEPTED_STATES = ['active', 'backup']


def build_commands(commands):
    """
    Defines the commands that can be executed through the syco.py shell script.
    """
    commands.add(
        "install-haproxy", install_haproxy,
        help="Install HA Proxy on the server.",
        password_list=[["haproxy-sps-ping", "haproxy"]]
    )
    commands.add(
        "uninstall-haproxy", uninstall_haproxy,
        help="Uninstall HA Proxy from the server."
    )


def install_haproxy(args):
    app.print_verbose("Install HA Proxy version: %d" % script_version)
    version_obj = version.Version("InstallHaproxy", script_version)
    version_obj.check_executed()

    setup_global_vars()

    # Validate all command line parameters.
    if len(sys.argv) < 4:
        print_killmessage()

    haproxy_env()
    haproxy_state()

    x("yum install -y tcl haproxy")
    iptables.add_haproxy_chain()
    iptables.save()
    _copy_certificate_files()
    _configure_haproxy()

    version_obj.mark_executed()


def setup_global_vars():
    """Initialize global variables from config files"""
    global cert_server, cert_server_path, cert_copy_to_path, SYCO_PLUGIN_PATH
    cert_server = config.general.get_cert_server_ip()
    cert_server_path = config.general.get_option('haproxy.remote_cert_path')
    cert_copy_to_path = config.general.get_option('haproxy.local_cert_path')
    SYCO_PLUGIN_PATH = app.get_syco_plugin_paths("/var/haproxy/").next()


def haproxy_env():
    """Get the haproxy environment from command line"""
    haproxy_env = sys.argv[2].lower()
    if haproxy_env not in get_environments():
        print_killmessage()
    return haproxy_env


def haproxy_state():
    """Get the haproxy state from command line"""
    haproxy_state = sys.argv[3].lower()
    if haproxy_state not in ACCEPTED_STATES:
        print_killmessage()
    return haproxy_state


def get_environments():
    """List all accepted environments from plugin folders"""
    environments = []
    for file in os.listdir(SYCO_PLUGIN_PATH):
        foo = re.search('(.*)\.haproxy\.cfg', file)
        if foo:
            environments.append(foo.group(1))
    return environments


def print_killmessage():
    print "Usage: syco install-haproxy <environment> <state>"
    print ""

    print " Valid environments:"
    for env in get_environments():
        print "    - " + env

    print " Valid states:"
    for env in ACCEPTED_STATES:
        print "    - " + env

    print " "
    sys.exit(0)


def _copy_certificate_files():
    copyfrom = "root@{0}".format(cert_server)
    copyremotefile = "{0}/{1}.pem".format(cert_server_path, haproxy_env())
    copylocalfile = "{0}/{1}.pem".format(cert_copy_to_path, haproxy_env())
    ssh.scp_from(copyfrom, copyremotefile, copylocalfile)


def _configure_haproxy():
    x("cp {0}haproxy.cfg {0}org.haproxy.cfg".format(HAPROXY_CONF_DIR))
    x("cp {0}/{1}.haproxy.cfg {2}haproxy.cfg".format(SYCO_PLUGIN_PATH, haproxy_env(), HAPROXY_CONF_DIR))
    x("cp {0}/error.html {1}error.html".format(SYCO_PLUGIN_PATH, HAPROXY_CONF_DIR))

    scopen.scOpen(HAPROXY_CONF).replace("${ENV_IP}", get_ip_address('eth1'))
    _configure_haproxy_state()

    if haproxy_env() == "farepayment":
        from installFarepayment import _configure_sps_password
        from installFarepayment import get_haproxy_sps_ping_password
        _configure_sps_password()

    _chkconfig("haproxy", "on")
    _service("haproxy", "restart")


def _configure_haproxy_state():
    if haproxy_state() == 'active':
        scopen.scOpen(HAPROXY_CONF).replace("${TCSTATE}", '')
        scopen.scOpen(HAPROXY_CONF).replace("${AVSTATE}", 'backup')
    else:
        scopen.scOpen(HAPROXY_CONF).replace("${TCSTATE}", 'backup')
        scopen.scOpen(HAPROXY_CONF).replace("${AVSTATE}", '')


def _chkconfig(service, command):
    x("/sbin/chkconfig {0} {1}".format(service, command))


def _service(service, command):
    x("/sbin/service {0} {1}".format(service, command))


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(
        fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24]
    )


def uninstall_haproxy(args):
    """
    Remove HA Proxy from the server.
    """
    app.print_verbose("Uninstall HA Proxy")

    setup_global_vars()

    # Validate all command line parameters.
    if len(sys.argv) != 3:
        print_killmessage()

    haproxy_env()

    iptables.del_haproxy_chain()
    iptables.save()
    _chkconfig("haproxy", "off")
    _service("haproxy", "stop")

    x("yum -y remove haproxy")
    x("rm -rf {0}*".format(HAPROXY_CONF_DIR))
    x("rm -rf {0}/{1}.pem".format(cert_copy_to_path, haproxy_env()))
