#!/usr/bin/env python
'''
This script will install HA Proxy on the targeted server.

This script is dependent on the following config files for this script to work.
    var/haproxy/[environment].haproxy.conf
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

CERT_SERVER = CERT_SERVER_PATH =  CERT_COPY_TO_PATH = SYCO_PLUGIN_PATH = None



def print_killmessage():
    print "Please specify environment"
    print_environments()
    print " "
    print "Usage: syco install-haproxy <environment>"
    print ""
    sys.exit(0)

def print_environments():
    print " Valid environments:"
    for env in ACCEPTED_HAPROXY_ENV:
        print "    - " + env

def get_environments():
    environments = []
    for file in os.listdir(SYCO_PLUGIN_PATH):
        foo = re.search('(.*)\.haproxy\.cfg', file)
        if foo:
            environments.append(foo.group(1))
    return environments

HAPROXY_CONF_DIR = "/etc/haproxy/"
ACCEPTED_HAPROXY_ENV = None

def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.
    '''
    commands.add("install-haproxy", install_haproxy, help="Install HA Proxy on the server.", password_list=[["haproxy-sps-ping", "haproxy"]])
    commands.add("uninstall-haproxy", uninstall_haproxy, help="Uninstall HA Proxy from the server.")

def _service(service,command):
    x("/sbin/service {0} {1}".format(service, command))

def _chkconfig(service,command):
    x("/sbin/chkconfig {0} {1}".format(service, command))

def install_haproxy(args):
    global CERT_SERVER, CERT_SERVER_PATH, CERT_COPY_TO_PATH, SYCO_PLUGIN_PATH, ACCEPTED_HAPROXY_ENV, HAPROXY_ENV

    CERT_SERVER = config.general.get_cert_server_ip()
    CERT_SERVER_PATH = config.general.get_option('haproxy.remote_cert_path')
    CERT_COPY_TO_PATH = config.general.get_option('haproxy.local_cert_path')
    SYCO_PLUGIN_PATH = app.get_syco_plugin_paths("/var/haproxy/").next()
    ACCEPTED_HAPROXY_ENV = get_environments()

    HAPROXY_ENV = sys.argv[2]

    if HAPROXY_ENV.lower() not in ACCEPTED_HAPROXY_ENV:
        print_killmessage()

    app.print_verbose("Install HA Proxy version: %d" % script_version)
    version_obj = version.Version("InstallHaproxy", script_version)
    version_obj.check_executed()
    os.chdir("/")

    x("yum install -y tcl haproxy")
    _configure_iptables()
    _copy_certificate_files()
    _configure_haproxy()

    version_obj.mark_executed()

def _configure_haproxy():
    x("mv {0}haproxy.cfg {0}org.haproxy.cfg".format(HAPROXY_CONF_DIR))
    x("cp {0}/{1}.haproxy.cfg {2}haproxy.cfg".format(SYCO_PLUGIN_PATH, HAPROXY_ENV, HAPROXY_CONF_DIR))
    x("cp {0}/error.html {1}error.html".format(SYCO_PLUGIN_PATH, HAPROXY_CONF_DIR))

    scopen.scOpen(HAPROXY_CONF_DIR + "haproxy.cfg").replace("${ENV_IP}", get_ip_address('eth1'))

    if HAPROXY_ENV == 'farepayment':
        _configure_farepayment_haproxy()

    _chkconfig("haproxy","on")
    _service("haproxy","restart")

def _configure_farepayment_haproxy():

    FAREPAYMENT_HAPROXY_DC = socket.gethostname()
    if FAREPAYMENT_HAPROXY_DC == 'farepayment-ha-tc':
        scopen.scOpen(HAPROXY_CONF_DIR + "haproxy.cfg").replace("${TCSTATE}",(''))
        scopen.scOpen(HAPROXY_CONF_DIR + "haproxy.cfg").replace("${AVSTATE}",('backup'))
    else:
        scopen.scOpen(HAPROXY_CONF_DIR + "haproxy.cfg").replace("${TCSTATE}",('backup'))
        scopen.scOpen(HAPROXY_CONF_DIR + "haproxy.cfg").replace("${AVSTATE}",(''))
    
    #SPS_PING_CREDENTIALS = password.get_haproxy_sps_password()
    SPS_PING_CREDENTIALS = app.get_custom_password("haproxy-sps-ping", "haproxy")
    BASE64CREDENTIALS = x("echo -n haproxy:{0} | base64 | tr -d '\n'".format(SPS_PING_CREDENTIALS))
    scopen.scOpen(HAPROXY_CONF_DIR + "haproxy.cfg").replace("${CREDENTIALS}",BASE64CREDENTIALS)


def _copy_certificate_files():
    copyfrom = "root@{0}".format(CERT_SERVER)
    copyremotefile = "{0}/{1}.pem".format(CERT_SERVER_PATH, HAPROXY_ENV)
    copylocalfile = "{0}/{1}.pem".format(CERT_COPY_TO_PATH, HAPROXY_ENV)
    ssh.scp_from(copyfrom, copyremotefile, copylocalfile)

def _configure_iptables():
    iptables.iptables("-A syco_input -p tcp -m multiport --dports 80,443 -j allowed_tcp")
    iptables.iptables("-A syco_output -p tcp -m multiport --dports 80,443 -j allowed_tcp")
    iptables.iptables("-A syco_input -p tcp -m multiport --dports 81,82,83,84 -j allowed_tcp")
    iptables.iptables("-A syco_output -p tcp -m multiport --dports 81,82,83,84 -j allowed_tcp")
    iptables.save()

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def uninstall_haproxy(args):
    '''
    Remove HA Proxy from the server.
    '''

    global HAPROXY_ENV
    HAPROXY_ENV = sys.argv[2]

    app.print_verbose("Uninstall HA Proxy")
    os.chdir("/")

    _chkconfig("haproxy","off")
    _service("haproxy","stop")

    x("yum -y remove haproxy")
    x("rm -rf {0}*".format(HAPROXY_CONF_DIR))
    x("rm -rf {0}/{1}.pem".format(CERT_COPY_TO_PATH, HAPROXY_ENV))
    iptables.iptables("-D syco_input -p tcp -m multiport --dports 80,443 -j allowed_tcp")
    iptables.iptables("-D syco_output -p tcp -m multiport --dports 80,443 -j allowed_tcp")
    iptables.iptables("-D syco_input -p tcp -m multiport --dports 81,82,83,84 -j allowed_tcp")
    iptables.iptables("-D syco_output -p tcp -m multiport --dports 81,82,83,84 -j allowed_tcp")
    iptables.save()


'''
End of HA Proxy installation script.
'''