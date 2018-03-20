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
from general import x, retrieve_from_server, get_front_nic_name, get_first_ip_from_nic, install_packages
import config
import iptables
import socket
import app
import password
import version
import scopen
import fcntl
import struct
import sys
import re
import install


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
        help="Install HA Proxy on the server."
    )
    commands.add(
        "uninstall-haproxy", uninstall_haproxy,
        help="Uninstall HA Proxy from the server."
    )


def install_haproxy(args):
    app.print_verbose("Install HA Proxy version: %d" % script_version)
    version_obj = version.Version("InstallHaproxy", script_version)
    version_obj.check_executed()

    # Prompt for syco pw early, certificate copy requires root pw
    app.get_root_password()

    setup_global_vars()

    # Validate all command line parameters.
    if len(args) != 3:
        print_killmessage()

    env = haproxy_env(args)
    state = haproxy_state(args)

    install_packages("tcl haproxy")
    iptables.add_haproxy_chain()
    iptables.save()
    _copy_certificate_files(env)
    _configure_haproxy(env, state)

    version_obj.mark_executed()


def setup_global_vars():
    """Initialize global variables from config files"""
    global cert_server, cert_server_path, cert_copy_to_path, SYCO_PLUGIN_PATH
    cert_server = config.general.get_cert_server_ip()
    cert_server_path = config.general.get_option('haproxy.remote_cert_path')
    cert_copy_to_path = config.general.get_option('haproxy.local_cert_path')
    SYCO_PLUGIN_PATH = app.get_syco_plugin_paths("/var/haproxy/").next()


def haproxy_env(args):
    """Get the haproxy environment from command line"""
    haproxy_env = args[1].lower()
    if haproxy_env not in get_environments():
        print_killmessage()
    return haproxy_env


def haproxy_state(args):
    """Get the haproxy state from command line"""
    haproxy_state = args[2].lower()
    if haproxy_state not in ACCEPTED_STATES:
        print_killmessage()
    return haproxy_state


def get_environments():
    """List all accepted environments from plugin folders"""
    environments = []
    for path in app.get_syco_plugin_paths("/var/haproxy/"):
        for f in os.listdir(path):
            foo = re.search('(.*)\.haproxy\.cfg', f)
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


def _copy_certificate_files(env):
    copyfrom = "root@{0}".format(cert_server)
    copyremotefile = "{0}/{1}.pem".format(cert_server_path, env)
    copylocalfile = "{0}/{1}.pem".format(cert_copy_to_path, env)
    retrieve_from_server(copyfrom, copyremotefile, copylocalfile, verify_local=[copylocalfile])


def _configure_haproxy(env, state):
    x("cp {0}haproxy.cfg {0}org.haproxy.cfg".format(HAPROXY_CONF_DIR))
    for path in app.get_syco_plugin_paths("/var/haproxy/"):
        app.print_verbose("Copy config files from %s" % path)
        x("cp {0}/{1}.haproxy.cfg {2}haproxy.cfg".format(path, env, HAPROXY_CONF_DIR))
        x("cp {0}/error.html {1}".format(path, HAPROXY_CONF_DIR))
        x("cp -R {0}/errors.xml {1}".format(path, HAPROXY_CONF_DIR))

    ifname = get_front_nic_name()
    scopen.scOpen(HAPROXY_CONF).replace("${ENV_IP}", get_first_ip_from_nic(ifname))
    if '${ENV_IP_ALIAS' in open(HAPROXY_CONF).read():
        scopen.scOpen(HAPROXY_CONF).replace("${ENV_IP_ALIAS}", get_first_ip_from_nic('{0}:1'.format(ifname)))

    _configure_haproxy_state(state)
    _configure_credentials(env)
    _chkconfig("haproxy", "on")
    _service("haproxy", "restart")
    _setup_monitoring()

    # chroot jail should not be accessible by anyone.
    x("chmod 000 /var/lib/haproxy")


def _configure_haproxy_state(state):
    if state == 'active':
        scopen.scOpen(HAPROXY_CONF).replace("${TCSTATE}", '')
        scopen.scOpen(HAPROXY_CONF).replace("${AVSTATE}", 'backup')
    else:
        scopen.scOpen(HAPROXY_CONF).replace("${TCSTATE}", 'backup')
        scopen.scOpen(HAPROXY_CONF).replace("${AVSTATE}", '')


def _configure_credentials(env):
    if '${CREDENTIALS}' in open(HAPROXY_CONF).read():
        pswd = password.get_custom_password("haproxy", env)
        base64pswd = x("echo -n haproxy:{0} | base64 | tr -d '\n'".format(pswd))
        scopen.scOpen(HAPROXY_CONF).replace("${CREDENTIALS}", base64pswd)


def _chkconfig(service, command):
    x("/sbin/chkconfig {0} {1}".format(service, command))


def _service(service, command):
    x("/sbin/service {0} {1}".format(service, command))


def _setup_monitoring():
    plugin = app.SYCO_PATH + "lib/nagios/plugins_nrpe/check_haproxy_stats.pl"
    installed_plugin = "/usr/lib64/nagios/plugins/check_haproxy_stats.pl"
    x("cp -f {0} {1}".format(plugin, installed_plugin))
    x("chown nrpe:nrpe {0}".format(installed_plugin))
    x("chmod 551 {0}".format(installed_plugin))
    x("restorecon {0}".format(installed_plugin))
    x("service nrpe restart")


def uninstall_haproxy(args):
    """
    Remove HA Proxy from the server.
    """
    app.print_verbose("Uninstall HA Proxy")

    setup_global_vars()

    # Validate all command line parameters.
    if len(args) != 3:
        print_killmessage()

    env = haproxy_env(args)

    iptables.del_haproxy_chain()
    iptables.save()
    _chkconfig("haproxy", "off")
    _service("haproxy", "stop")

    x("yum -y remove haproxy")
    x("rm -rf {0}*".format(HAPROXY_CONF_DIR))
    x("rm -rf {0}/{1}.pem".format(cert_copy_to_path, env))
