#!/usr/bin/env python
'''
This script will install Keepalived standalone on the targeted server.

This script is dependent on the following config files for this script to work.
    var/keepalived/[environment].keepalived.conf
'''

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

script_version = 1

SYCO_PLUGIN_PATH = None

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
        foo = re.search('(.*)\.keepalived\.cfg', file)
        if foo:
            environments.append(foo.group(1))
    return environments

KA_CONF_DIR = "/etc/keepalived/"
ACCEPTED_KA_ENV = None

def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.
    '''
    commands.add("install-keepalived", install_keepalived, help="Install Keepalived on the server.")
    commands.add("uninstall-keepalived", uninstall_keepalived, help="Uninstall Keepalived from the server.")

def _service(service,command):
    x("/sbin/service {0} {1}".format(service, command))

def _chkconfig(service,command):
    x("/sbin/chkconfig {0} {1}".format(service, command))

def install_keepalived(args):
    global SYCO_PLUGIN_PATH, ACCEPTED_KA_ENV

    SYCO_PLUGIN_PATH = app.get_syco_plugin_paths("/var/keepalived/").next()
    ACCEPTED_KA_ENV = get_environments()

    if len(sys.argv) != 3:
        print_killmessage()
    else:
        KA_ENV = sys.argv[2]

    if KA_ENV.lower() not in ACCEPTED_KA_ENV:
        print_killmessage()

    app.print_verbose("Install Keepalived version: %d" % script_version)
    version_obj = version.Version("InstallKeepalived", script_version)
    version_obj.check_executed()
    os.chdir("/")

    x("yum install -y keepalived")
    _configure_iptables()
    _configure_keepalived()

    version_obj.mark_executed()

def _configure_keepalived():
    '''
    * Keepalived needs the possibility to bind on non local adresses.
    * It will replace the variables in the config file with the hostname.
    * It is not environmental dependent and can be installed on any server.
    '''
    x("echo 'net.ipv4.ip_nonlocal_bind = 1' >> /etc/sysctl.conf")
    x("sysctl -p")
    x("mv {0}keepalived.conf {0}org.keepalived.conf".format(KA_CONF_DIR))
    x("cp {0}/{1}.keepalived.conf {2}keepalived.conf".format(SYCO_PLUGIN_PATH, HAPROXY_ENV, KA_CONF_DIR))
    scopen.scOpen(KA_CONF_DIR + "keepalived.conf").replace("${KA_SERVER_NAME_UP}", socket.gethostname().upper())
    scopen.scOpen(KA_CONF_DIR + "keepalived.conf").replace("${KA_SERVER_NAME_DN}", socket.gethostname().lower())
    _chkconfig("keepalived","on")
    _service("keepalived","restart")

def _configure_iptables():
    '''
    * Keepalived uses multicast and VRRP protocol to talk to the nodes and need to
        be opened. So first we remove the multicast blocks and then open them up.
    * VRRP is known as Protocol 112 in iptables.
    '''
    iptables.iptables("-D multicast_packets -s 224.0.0.0/4 -j DROP")
    iptables.iptables("-D multicast_packets -d 224.0.0.0/4 -j DROP")
    iptables.iptables("-A multicast_packets -d 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-A multicast_packets -s 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-A syco_input -p 112 -i eth1 -j ACCEPT")
    iptables.iptables("-A syco_output -p 112 -o eth1 -j ACCEPT")
    iptables.save()

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def uninstall_keepalived(args=""):
    '''
    Remove Keepalived from the server.
    '''
    app.print_verbose("Uninstall Keepalived")
    os.chdir("/")

    _chkconfig("keepalived","off")
    _service("keepalived","stop")

    x("yum -y remove keepalived")
    x("rm -rf {0}*".format(KA_CONF_DIR))
    iptables.iptables("-D multicast_packets -d 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-D multicast_packets -s 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-A multicast_packets -s 224.0.0.0/4 -j DROP")
    iptables.iptables("-A multicast_packets -d 224.0.0.0/4 -j DROP")
    iptables.iptables("-D syco_input -p 112 -i eth1 -j ACCEPT")
    iptables.iptables("-D syco_output -p 112 -o eth1 -j ACCEPT")
    iptables.save()

'''
End of Keepalived installation script.
'''