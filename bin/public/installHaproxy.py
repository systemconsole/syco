#!/usr/bin/env python
'''
This script will install HA Proxy on the targeted server.

This script is dependent on the following config files in syco-private for this script to work.
    var/haproxy/[enviroment].keepalived.conf
    var/haproxy/[enviroment].haproxy.conf
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
import getopt

script_version = 1

if len(sys.argv) != 3:
    print_killmessage()

SYCO_FO_PATH = app.SYCO_PATH + "usr/syco-private/"
HAPROXY_CONF_DIR = "/etc/haproxy/"
HHAPROXY_ENV = sys.argv[2]
KEEPALIVED_CONF_DIR = "/etc/keepalived/"

def print_killmessage():
    print "Enviroment needed\n"
    print "Usage: syco install-haproxy <env>"
    print "Valid enviroments: eff, rentalfront"
    sys.exit(0)


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.
    '''
    commands.add("install-haproxy", install_haproxy, help="Install HA Proxy on the server.")
    commands.add("uninstall-haproxy", uninstall_haproxy, help="Uninstall HA Proxy from the server.")

def _service(service,command):
    x("/sbin/service {0} {1}".format(service, command))

def _chkconfig(service,command):
    x("/sbin/chkconfig {0} {1}".format(service, command))

def install_haproxy(args):

    if HAPROXY_ENV.lower() != ("eff" or "rentalfront"):
        print_killmessage()

    app.print_verbose("Install HA Proxy version: %d" % script_version)
    version_obj = version.Version("InstallHaproxy", script_version)
    version_obj.check_executed()
    os.chdir("/")

    x("yum install -y tcl haproxy keepalived")
    _configure_iptables()
    _configure_keepalived()
    _configure_haproxy()
    _copy_certificate_files()

    x("sysctl -p")
    version_obj.mark_executed()

def _configure_keepalived():
    '''
    * Keepalived needs the possibility to bind on non local adresses.
    * It will replace the variables in the config file with the hostname.
    * It is not enviromental dependent and can be installed on any server.
    '''
    x("echo 'net.ipv4.ip_nonlocal_bind = 1' >> /etc/sysctl.conf")
    x("mv {0}keepalived.conf {0}org.keepalived.conf".format(KEEPALIVED_CONF_DIR))
    x("cp {0}var/haproxy/{1}.keepalived.conf {2}keepalived.conf".format(SYCO_FO_PATH, HAPROXY_ENV, KEEPALIVED_CONF_DIR))
    scopen.scOpen(KEEPALIVED_CONF_DIR + "keepalived.conf").replace("${HAPROXY_SERVER_NAME_UP}", socket.gethostname().upper())
    scopen.scOpen(KEEPALIVED_CONF_DIR + "keepalived.conf").replace("${HAPROXY_SERVER_NAME_DN}", socket.gethostname().lower())
    _chkconfig("keepalived","on")
    _service("keepalived","restart")

def _configure_haproxy():
    x("mv {0}haproxy.cfg {0}org.haproxy.cfg".format(KEEPALIVED_CONF_DIR))
    x("cp {0}var/haproxy/{1}.haproxy.cfg {2}haproxy.cfg".format(SYCO_FO_PATH, HAPROXY_ENV, HAPROXY_CONF_DIR))
    x("cp {0}var/haproxy/error.html {2}error.html".format(SYCO_FO_PATH, HAPROXY_CONF_DIR))

    scopen.scOpen(HAPROXY_CONF_DIR + "haproxy.cfg").replace("${ENV_IP}", get_ip_address('eth1'))

    _chkconfig("haproxy","on")
    _service("haproxy","restart")

def _copy_certificate_files():
    '''
    Currently the certificate must be copied manually during a fresh install since the PEM format
    is a littlebit different. Support for this will come at a later time. This will also cause the
    haproxy process to fail startup after installation if it is terminating HTTPS.

    Enviroments that need certificate:
      * EFF (Wildcardcert *.myehtrip.com)
      * Rentalfront (Wildcartcert *.fareoffice.com)
    '''
    if HAPROXY_ENV == "eff":
        #Code to copy and create EFF Certificate PEM to HA Proxy will be here.
        copy = 0
    if HAPROXY_ENV == "rentalfront":
        #Code to copy and create RF Certificate PEM to HA Proxy will be here.
        copy = 0

def _configure_iptables():
    '''
    * Keepalived uses multicast and VRRP protocol to talk to the nodes and need to
        be opened. So first we remove the multicast blocks and then open them up.
    * VRRP is known as Protocol 112 in iptables.
    '''
    iptables.iptables("-A syco_input -p tcp -m multiport --dports 80,443 -j allowed_tcp")
    iptables.iptables("-A syco_output -p tcp -m multiport --dports 80,443 -j allowed_tcp")
    iptables.iptables("-A syco_input -p tcp -m multiport --dports 81,82,83,84 -j allowed_tcp")
    iptables.iptables("-A syco_output -p tcp -m multiport --dports 81,82,83,84 -j allowed_tcp")
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

def uninstall_haproxy():
    '''
    Remove HA Proxy from the server.
    '''
    app.print_verbose("Uninstall HA Proxy")
    os.chdir("/")

    _chkconfig("haproxy","off")
    _service("haproxy","stop")
    _chkconfig("keepalived","off")
    _service("keepalived","stop")

    x("yum -y remove haproxy keepalived")
    x("rm -rf {0}*".format(HAPROXY_CONF_DIR))
    x("rm -rf {0}*".format(KEEPALIVED_CONF_DIR))

    iptables.iptables("-D syco_input -p tcp -m multiport --dports 80,443 -j allowed_tcp")
    iptables.iptables("-D syco_output -p tcp -m multiport --dports 80,443 -j allowed_tcp")
    iptables.iptables("-D syco_input -p tcp -m multiport --dports 81,82,83,84 -j allowed_tcp")
    iptables.iptables("-D syco_output -p tcp -m multiport --dports 81,82,83,84 -j allowed_tcp")
    iptables.iptables("-D multicast_packets -d 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-D multicast_packets -s 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-D syco_input -p 112 -i eth1 -j ACCEPT")
    iptables.iptables("-D syco_output -p 112 -o eth1 -j ACCEPT")
    iptables.save()


'''
End of HA Proxy installation script.
'''
