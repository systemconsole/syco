#!/usr/bin/env python
"""
This script will install Keepalived standalone on the targeted server.

This script is dependent on the following config files for this script to work.
    var/keepalived/[environment].keepalived.conf
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
from general import x
import socket
import app
import version
import scopen
import fcntl
import struct
import sys
import re
from iptables import MulticastConfig

script_version = 1

SYCO_PLUGIN_PATH = None
KA_CONF_DIR = "/etc/keepalived/"
ACCEPTED_KA_ENV = None
ka_env = None


def print_killmessage():
    print "Please specify environment"
    print_environments()
    print " "
    print "Usage: syco install-keepalived <environment>"
    print ""
    sys.exit(0)


def print_environments():
    print " Valid environments:"
    for env in ACCEPTED_KA_ENV:
        print "    - " + env


def get_environments():
    environments = []
    for file in os.listdir(SYCO_PLUGIN_PATH):
        foo = re.search('(.*)\.keepalived\.conf', file)
        if foo:
            environments.append(foo.group(1))
    return environments


def build_commands(commands):
    """
    Defines the commands that can be executed through the syco.py shell script.
    """
    commands.add("install-keepalived", install_keepalived, help="Install Keepalived on the server.")
    commands.add("uninstall-keepalived", uninstall_keepalived, help="Uninstall Keepalived from the server.")


def _service(service,command):
    x("/sbin/service {0} {1}".format(service, command))


def _chkconfig(service,command):
    x("/sbin/chkconfig {0} {1}".format(service, command))


def install_keepalived(args):
    global SYCO_PLUGIN_PATH, ACCEPTED_KA_ENV, ka_env

    SYCO_PLUGIN_PATH = app.get_syco_plugin_paths("/var/keepalived/").next()
    ACCEPTED_KA_ENV = get_environments()

    if len(args) != 2:
        print_killmessage()
    else:
        ka_env = args[1]

    if ka_env.lower() not in ACCEPTED_KA_ENV:
        print_killmessage()

    app.print_verbose("Install Keepalived version: %d" % script_version)
    version_obj = version.Version("InstallKeepalived", script_version)
    version_obj.check_executed()
    os.chdir("/")

    x("yum install -y keepalived")
    _configure_keepalived()

    version_obj.mark_executed()


def _configure_keepalived():
    """
    * Keepalived needs the possibility to bind on non local adresses.
    * It will replace the variables in the config file with the hostname.
    * It is not environmental dependent and can be installed on any server.
    """
    x("echo 'net.ipv4.ip_nonlocal_bind = 1' >> /etc/sysctl.conf")
    x("sysctl -p")
    x("mv {0}keepalived.conf {0}org.keepalived.conf".format(KA_CONF_DIR))
    x("cp {0}/{1}.keepalived.conf {2}keepalived.conf".format(SYCO_PLUGIN_PATH, ka_env, KA_CONF_DIR))
    scopen.scOpen(KA_CONF_DIR + "keepalived.conf").replace("${KA_SERVER_NAME_UP}", socket.gethostname().upper())
    scopen.scOpen(KA_CONF_DIR + "keepalived.conf").replace("${KA_SERVER_NAME_DN}", socket.gethostname().lower())
    _chkconfig("keepalived","on")
    _service("keepalived","restart")


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def uninstall_keepalived(args=""):
    """
    Remove Keepalived from the server.
    """
    app.print_verbose("Uninstall Keepalived")
    os.chdir("/")

    _chkconfig("keepalived","off")
    _service("keepalived","stop")

    x("yum -y remove keepalived")
    x("rm -rf {0}*".format(KA_CONF_DIR))


def get_keepalived_fw_config():
    return [
        MulticastConfig("224.0.0.0/8", "vrrp")
    ]

"""
End of Keepalived installation script.
"""