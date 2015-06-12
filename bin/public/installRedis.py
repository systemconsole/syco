#!/usr/bin/env python
'''
This script will install Redis on the targeted server.

This script is dependent on the following config files in syco-private for this script to work.
    var/redis/redis.conf
    var/redis/keepalived.conf
    var/redis/check-redis

It is also dependent on the EPEL repo since Redis is not available on CentOS official Repo.
'''

__author__ = "David Skeppstedt"
__copyright__ = "Copyright 2014, Fareoffice CRS AB"
__maintainer__ = "David Skeppstedt"
__email__ = "davske@fareoffice.com"
__credits__ = ["Daniel Lindh, Mattias Hemmingsson, Kristoffer Borgstrom"]
__license__ = "???"
__version__ = "2.4.10"
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

script_version = 1

#Setting paths
SYCO_FO_PATH = app.SYCO_PATH + "usr/syco-private/"
REDIS_SCRIPT_DIR = "/usr/bin/"
REDIS_CONF_DIR = "/etc/"
KEEPALIVED_CONF_DIR = "/etc/keepalived/"

def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.
    '''

    commands.add("install-redis", install_redis, help="Install Redis on the server.")
    commands.add("uninstall-redis", uninstall_redis, help="Uninstall Redis from the server.")

def install_redis(args):
    app.print_verbose("Install Redis version: %d" % script_version)
    version_obj = version.Version("InstallRedis", script_version)
    version_obj.check_executed()
    os.chdir("/")

    '''
    Install the packages and then configure them.
    '''

    # Installation fails using the install.package function, needs to debug further before adding again. Workaround with manual command.
    #install.package("tcl redis keepalived")
    x("yum install -y tcl redis keepalived")
    _configure_iptables()
    _configure_keepalived()
    _configure_redis()

    x("sysctl -p")

    version_obj.mark_executed()


def _configure_keepalived():
    '''
    * Keepalived needs the possibility to bind on non local adresses.
    * It will replace the variables in the config file with the hostname.
    * It is not enviromental dependent and can be installed on any server.
    '''

    x("echo 'net.ipv4.ip_nonlocal_bind = 1' >> /etc/sysctl.conf")
    x("mv {0}keepalived.conf {1}org.keepalived.conf".format(KEEPALIVED_CONF_DIR, KEEPALIVED_CONF_DIR))
    x("cp {0}var/redis/keepalived.conf {1}keepalived.conf".format(SYCO_FO_PATH, KEEPALIVED_CONF_DIR))
    scopen.scOpen(KEEPALIVED_CONF_DIR + "keepalived.conf").replace("${REDIS_SERVER_NAME_UP}", socket.gethostname().upper())
    scopen.scOpen(KEEPALIVED_CONF_DIR + "keepalived.conf").replace("${REDIS_SERVER_NAME_DN}", socket.gethostname().lower())
    _chkconfig("keepalived","on")
    _service("keepalived","restart")


def _configure_redis():
    '''
    * Redis needs to be able to overcommit memory or it will fail during replication.
    * It does not have any enviromental specific configuration and can be installed on any server or enviroment.
    * redis-check is the script keepalived uses in order to setup master/slave replication.
    '''

    x("echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf")
    x("mv {0}redis.conf {1}org.redis.conf".format(REDIS_CONF_DIR, REDIS_CONF_DIR))
    x("cp {0}var/redis/redis.conf {1}redis.conf".format(SYCO_FO_PATH, REDIS_CONF_DIR))
    x("cp {0}var/redis/redis-check {1}redis-check".format(SYCO_FO_PATH, REDIS_SCRIPT_DIR))
    x("chmod 755 {0}redis-check".format(REDIS_SCRIPT_DIR))
    scopen.scOpen(REDIS_CONF_DIR + "redis.conf").replace("${REDIS_PASSWORD}", password.get_redis_production_password())
    scopen.scOpen(REDIS_SCRIPT_DIR + "redis-check").replace("${REDIS_PASSWORD}", password.get_redis_production_password())
    _chkconfig("redis","on")
    _service("redis","restart")


def _service(service,command):
    x("/sbin/service {0} {1}".format(service, command))


def _chkconfig(service,command):
    x("/sbin/chkconfig {0} {1}".format(service, command))


def _configure_iptables(args):
    '''
    * Keepalived uses multicast and VRRP protocol to talk to the nodes and need to 
        be opened. So first we remove the multicast blocks and then open them up.
    * VRRP is known as Protocol 112 in iptables.
    * Redis uses port 6379 and need to be opened.
    '''

    iptables.iptables("-A syco_input -p tcp -m multiport --dports 6379 -j allowed_tcp")
    iptables.iptables("-A syco_output -p tcp -m multiport --dports 6379 -j allowed_tcp")
    iptables.iptables("-D multicast_packets -s 224.0.0.0/4 -j DROP")
    iptables.iptables("-D multicast_packets -d 224.0.0.0/4 -j DROP")
    iptables.iptables("-A multicast_packets -d 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-A multicast_packets -s 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-A syco_input -p 112 -i eth1 -j ACCEPT")
    iptables.iptables("-A syco_output -p 112 -o eth1 -j ACCEPT")
    iptables.save()


def uninstall_redis(args):
    '''
    Remove Redis from the server
    '''
    #return
    app.print_verbose("Uninstall Redis")

    os.chdir("/")

    _chkconfig("redis","off")
    _service("redis","stop")
    _chkconfig("keepalived","on")
    _service("keepalived","restart")

    x("yum -y remove redis keepalived")
    x("rm -rf {0}redis.conf".format(REDIS_CONF_DIR))
    x("rm -rf {0}redis.conf.rpmsave".format(REDIS_CONF_DIR))
    x("rm -rf {0}*".format(KEEPALIVED_CONF_DIR))

    iptables.iptables("-D syco_input -p tcp -m multiport --dports 6379 -j allowed_tcp")
    iptables.iptables("-D syco_output -p tcp -m multiport --dports 6379 -j allowed_tcp")
    iptables.iptables("-D multicast_packets -d 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-D multicast_packets -s 224.0.0.0/8 -j ACCEPT")
    iptables.iptables("-D syco_input -p 112 -i eth1 -j ACCEPT")
    iptables.iptables("-D syco_output -p 112 -o eth1 -j ACCEPT")
    iptables.iptables("-A multicast_packets -s 224.0.0.0/4 -j DROP")
    iptables.iptables("-A multicast_packets -d 224.0.0.0/4 -j DROP")
    iptables.save()


'''
End of Redis installation script.
'''
