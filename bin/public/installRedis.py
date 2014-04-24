#!/usr/bin/env python
'''
This script will install Redis on the targeted server.

'''

__author__ = "davske@fareoffice.com"
__copyright__ = "Copyright 2014, The System Console project"
__maintainer__ = "David Skeppstedt"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "2.8.9"
__status__ = "Production"

import os
import shutil
import stat
import sys
import time
import traceback
import config
import iptables
import install
from config import get_servers, host
import app
from general import x, download_file, md5checksum, get_install_dir
import version


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-redis", install_redis, help="Install Redis on the server.")
  commands.add("uninstall-redis", uninstall_redis, help="Uninstall Redis from the server.")

def install_redis(args):
  '''
  Redis Installation

  '''
  #return
  app.print_verbose("Install Redis version: %d" % script_version)
  version_obj = version.Version("InstallRedis", script_version)
  version_obj.check_executed()

  os.chdir("/")
  install.package("tcl redis keepalived")
  
  # Add iptables rules.
  iptables.iptables("-A syco_input -p tcp -m multiport --dports 6379 -j allowed_tcp") # Redis listens to port 6379
  iptables.iptables("-A syco_output -p tcp -m multiport --dports 6379 -j allowed_tcp") # Redis listens to port 6379
  iptables.iptables("-A syco_input -i eth1 -d 224.0.0.0/8 -j ACCEPT") #M ulticast needed to be unblocked for VRRP protocol to work.
  iptables.iptables("-A syco_input -p 112 -i eth1 -j ACCEPT") # Open up for VRRP Protocol (IP Protocol 112)
  iptables.iptables("-A syco_output -p 112 -o eth1 -j ACCEPT") # Open up for VRRP Protocol (IP Protocol 112)
  iptables.save()
  
  #Configure Redis
  x("mv /etc/redis.conf /etc/org.redis.conf")
  x("cp /opt/syco/usr/syco-private/var/redis/redis.conf /etc/redis.conf")

  # Configure Keepalived
  x("echo 'net.ipv4.ip_nonlocal_bind = 1' >> /etc/sysctl.conf")
  x("mv /etc/keepalived/keepalived.conf /etc/keepalived/org.keepalived.conf")
  x("cp /opt/syco/usr/syco-private/var/redis/keepalived.conf /etc/keepalived/keepalived.conf")

  # Start the services.
  x("/sbin/chkconfig --level 3 keepalived on")
  x("service keepalived restart")
  x("/sbin/chkconfig --level 3 redis on")
  x("service redis restart")

  version_obj.mark_executed()

def uninstall_redis(args):
  '''
  Remove Redis from the server

  '''
  #return
  app.print_verbose("Uninstall Redis")

  os.chdir("/")
  x("/sbin/chkconfig --level 3 redis off")
  x("service redis stop")
  x("/sbin/chkconfig --level 3 keepalived off")
  x("service keepalived stop")
  x("yum -y remove redis keepalived")
  x("rm -rf /etc/redis.conf")
  x("rm -rf /etc/redis.conf.rpmsave")
  x("rm -rf /etc/keepalived/*")
  iptables.iptables("-D syco_input -p tcp -m multiport --dports 6379 -j allowed_tcp")
  iptables.iptables("-D syco_output -p tcp -m multiport --dports 6379 -j allowed_tcp")
  iptables.iptables("-D syco_input -i eth1 -d 224.0.0.0/8 -j ACCEPT")
  iptables.iptables("-D syco_input -p 112 -i eth1 -j ACCEPT")
  iptables.iptables("-D syco_output -p 112 -o eth1 -j ACCEPT")
  iptables.save()