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
  return
  app.print_verbose("Install Redis version: %d" % script_version)
  version_obj = version.Version("InstallRedis", script_version)
  version_obj.check_executed()

  os.chdir("/")
  x("yum -y install tcl redis")
  x("/sbin/iptables -A syco_input -p tcp -m multiport --dports 6379 -j allowed_tcp")
  x("/sbin/iptables -A syco_output -p tcp -m multiport --dports 6379 -j allowed_tcp")
  x("mv /etc/redis.conf /etc/org.redis.conf")
  x("cp /opt/syco/usr/syco-private/var/redis/redis.conf /etc/redis.conf")
  x("service redis restart")

  version_obj.mark_executed()

def uninstall_redis(args):
  '''
  Remove Redis from the server

  '''
  return
  app.print_verbose("Uninstall Redis")

  os.chdir("/")

  x("service redis stop")
  x("yum -y remove redis")
  x("rm -rf /etc/redis.conf")
