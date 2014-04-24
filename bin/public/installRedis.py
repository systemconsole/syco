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

import app
import general
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
  commands.add("uninstall-redis", uninstall_redis, help="uninstall Redis and all certs on the server.")

def install_redis(args):
  '''
  Redis Installation

  '''
  return
  app.print_verbose("Install Redis version: %d" % script_version)
  version_obj = version.Version("InstallRedis", script_version)
  version_obj.check_executed()

  #if os.path.exists('/etc/ssl/ca/private/ca.key'):
  #  app.print_verbose("CA is already installed")
  #else:
    #making folders
    #creating certs
    #os.chdir("/etc/ssl")
    #general.shell_exec("openssl genrsa -out ca/private/ca.key 4096")
    #general.shell_exec("openssl req -new -key ca/private/ca.key -out ca/ca.csr -subj '/O=syco/OU=System Console Project/CN=systemconsole.github.com'")
    #general.shell_exec("openssl x509 -req -days 365 -in ca/ca.csr -signkey ca/private/ca.key -out ca/ca.crt ")


  version_obj.mark_executed()

def uninstall_redis(args):
  '''
  Remove Redis from the server

  '''
  return
  app.print_verbose("Uninstall Redis")

  #if (os.path.exists('/etc/ssl/ca/private/ca.key')):
  #  general.shell_exec("rm -rf /etc/ssl/")
  #version_obj = version.Version("InstallCa", script_version)
  #version_obj.mark_uninstalled()


