#!/usr/bin/env python
'''
This script will install HA Proxy on the targeted server.

This script is dependent on the following config files for this script to work.
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
import re
import glob
import fnmatch

script_version = 1

HAPROXY_CONF_DIR = "/etc/haproxy/"
KEEPALIVED_CONF_DIR = "/etc/keepalived/"

### MOVE TO SEPARATE CONFIG FILE ###

# Better solution to hide this reference?
SYCO_FO_PATH = app.SYCO_PATH + "usr/syco-private/"

# Do we have a cert to copy or plain HTTP, and where to copy from.
HAPROXY_ENV_CERT = True
CERT_SERVER = "10.101.2.2"  ### general.install_server ?
CERT_SERVER_PATH = "/etc/syco/ssl/haproxy-ssl"
CERT_COPY_TO_PATH = "/etc/ssl/certs"

# Which enviroments do we accept?
ACCEPTED_HAPROXY_ENV = [
    'eff',
    'rentalfront'
]

### END MOVE ###

def print_killmessage():
    print "Please specify enviroment"
    print_enviroments()
    print " "
    print "Usage: syco install-haproxy <enviroment>"
    print ""
    sys.exit(0)

def print_enviroments():
    print " Valid enviroments:"
    for env in ACCEPTED_HAPROXY_ENV:
        print "    - " + env

def get_enviroments():


    if (os.access(app.SYCO_USR_PATH, os.F_OK)):
        for plugin in os.listdir(app.SYCO_USR_PATH):
            #print plugin
            plugin_path = os.path.abspath(app.SYCO_USR_PATH + plugin + "/var/haproxy/")
            if (os.access(plugin_path, os.F_OK)):
                enviroment_path = plugin_path


    files=[]
    for file in os.listdir(enviroment_path):
        foo = re.search('(.*)\.haproxy\.cfg', file)
        if foo:
            files.append(foo.group(1))
    print files

print get_enviroments()
sys.exit()


if len(sys.argv) != 3:
    print_killmessage()
else:
    HAPROXY_ENV = sys.argv[2]

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
    if HAPROXY_ENV.lower() not in ACCEPTED_HAPROXY_ENV:
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

    version_obj.mark_executed()

def _configure_keepalived():
    '''
    * Keepalived needs the possibility to bind on non local adresses.
    * It will replace the variables in the config file with the hostname.
    * It is not enviromental dependent and can be installed on any server.
    '''
    x("echo 'net.ipv4.ip_nonlocal_bind = 1' >> /etc/sysctl.conf")
    x("sysctl -p")
    x("mv {0}keepalived.conf {0}org.keepalived.conf".format(KEEPALIVED_CONF_DIR))
    x("cp {0}var/haproxy/{1}.keepalived.conf {2}keepalived.conf".format(SYCO_FO_PATH, HAPROXY_ENV, KEEPALIVED_CONF_DIR))
    scopen.scOpen(KEEPALIVED_CONF_DIR + "keepalived.conf").replace("${HAPROXY_SERVER_NAME_UP}", socket.gethostname().upper())
    scopen.scOpen(KEEPALIVED_CONF_DIR + "keepalived.conf").replace("${HAPROXY_SERVER_NAME_DN}", socket.gethostname().lower())
    _chkconfig("keepalived","on")
    _service("keepalived","restart")

def _configure_haproxy():
    x("mv {0}haproxy.cfg {0}org.haproxy.cfg".format(HAPROXY_CONF_DIR))
    x("cp {0}var/haproxy/{1}.haproxy.cfg {2}haproxy.cfg".format(SYCO_FO_PATH, HAPROXY_ENV, HAPROXY_CONF_DIR))
    x("cp {0}var/haproxy/error.html {1}error.html".format(SYCO_FO_PATH, HAPROXY_CONF_DIR))

    scopen.scOpen(HAPROXY_CONF_DIR + "haproxy.cfg").replace("${ENV_IP}", get_ip_address('eth1'))

    _chkconfig("haproxy","on")
    _service("haproxy","restart")

def _copy_certificate_files():
    if HAPROXY_ENV_CERT == True:
        #x("scp {0}:{1}/{3}.pem {2}/{3}.pem".format(CERT_SERVER, CERT_SERVER_PATH, CERT_COPY_TO_PATH, HAPROXY_ENV))
        copy = 1

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

def uninstall_haproxy(args=""):
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
