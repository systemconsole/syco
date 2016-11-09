#!/usr/bin/env python
"""
This script will install Keepalived standalone on the targeted server.

This script is dependent on the following config files for this script to work.
    var/keepalived/[environment].keepalived.conf
"""

__author__ = "David Skeppstedt"
__copyright__ = "Copyright 2014, Fareoffice CRS AB"
__maintainer__ = "Kristofer Borgstrom"
__email__ = "davske@fareoffice.com"
__credits__ = ["Daniel Lindh, Mattias Hemmingsson, Kristoffer Borgstrom"]
__license__ = "???"
__version__ = "1.5"
__status__ = "Production"

import os
from general import x, install_packages, get_front_nic_name
from iptables import iptables, save
from augeas import Augeas
import socket
import app
import version
import scopen
import fcntl
import struct
import sys
import re
import general
import config
import install

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
    for f in os.listdir(SYCO_PLUGIN_PATH):
        foo = re.search('(.*)\.keepalived\.conf', f)
        if foo:
            environments.append(foo.group(1))
    return environments


def build_commands(commands):
    """
    Defines the commands that can be executed through the syco.py shell script.
    """
    commands.add("install-keepalived", install_keepalived, help="Install Keepalived on the server.")
    commands.add("uninstall-keepalived", uninstall_keepalived, help="Uninstall Keepalived from the server.")


def iptables_setup():
    """Called from iptables.py"""
    del_iptables_chain()
    if os.path.exists('/etc/keepalived/keepalived.conf'):
        add_iptables_chain()


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

    install.epel_repo()
    install_packages("keepalived python-netifaces")
    _configure_keepalived()

    # Adding iptables rules
    iptables_setup()
    save()

    version_obj.mark_executed()


def _configure_keepalived():
    """
    * Keepalived needs the possibility to bind on non local adresses.
    * It will replace the variables in the config file with the hostname.
    * It is not environmental dependent and can be installed on any server.
    """
    augeas = Augeas(x)
    augeas.set_enhanced("/files/etc/sysctl.conf/net.ipv4.ip_nonlocal_bind", "1")
    x("sysctl -p")
    x("mv {0}keepalived.conf {0}org.keepalived.conf".format(KA_CONF_DIR))
    x("cp {0}/{1}.keepalived.conf {2}keepalived.conf".format(SYCO_PLUGIN_PATH, ka_env, KA_CONF_DIR))
    scopen.scOpen(KA_CONF_DIR + "keepalived.conf").replace("${KA_SERVER_NAME_UP}", socket.gethostname().upper())
    scopen.scOpen(KA_CONF_DIR + "keepalived.conf").replace("${KA_SERVER_NAME_DN}", socket.gethostname().lower())
    _chkconfig("keepalived","on")
    _service("keepalived","restart")


def del_iptables_chain():
    app.print_verbose("Delete iptables chain for keepalived")

    iptables("-D syco_output -p ALL -j keepalived_output", general.X_OUTPUT_CMD)
    iptables("-F keepalived_output", general.X_OUTPUT_CMD)
    iptables("-X keepalived_output", general.X_OUTPUT_CMD)

    iptables("-D syco_output -p ALL -j keepalived_output", general.X_OUTPUT_CMD)
    iptables("-F keepalived_input", general.X_OUTPUT_CMD)
    iptables("-X keepalived_input", general.X_OUTPUT_CMD)

    iptables("-D multicast_packets -d 224.0.0.0/8 -j ACCEPT", general.X_OUTPUT_CMD)
    iptables("-D multicast_packets -s 224.0.0.0/8 -j ACCEPT", general.X_OUTPUT_CMD)
    iptables("-A multicast_packets -s 224.0.0.0/4 -j DROP")
    iptables("-A multicast_packets -d 224.0.0.0/4 -j DROP")


def add_iptables_chain():
    """
    * Keepalived uses multicast and VRRP protocol to talk to the nodes and need to
        be opened. So first we remove the multicast blocks and then open them up.
    * VRRP is known as Protocol 112 in iptables.
    """
    app.print_verbose("Add iptables chain for keepalived")
    iptables("-N keepalived_output")
    iptables("-A syco_output -p ALL -j keepalived_output")
    iptables("-N keepalived_input")
    iptables("-A syco_input -p ALL -j keepalived_input")

    front_nic = get_front_nic_name()

    iptables("-A keepalived_input -p 112 -i {0} -j ACCEPT".format(front_nic))
    iptables("-A keepalived_output -p 112 -o {0} -j ACCEPT".format(front_nic))

    iptables("-D multicast_packets -s 224.0.0.0/4 -j DROP", general.X_OUTPUT_CMD)
    iptables("-D multicast_packets -d 224.0.0.0/4 -j DROP", general.X_OUTPUT_CMD)
    iptables("-A multicast_packets -d 224.0.0.0/8 -j ACCEPT")
    iptables("-A multicast_packets -s 224.0.0.0/8 -j ACCEPT")


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
    del_iptables_chain()
    iptables.save()