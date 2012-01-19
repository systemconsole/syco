#!/usr/bin/env python
'''
TODO, THIS FILE IS NOT READY TO USE.

'''

__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
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
  commands.add("install-ca", install_ca, help="Install CA on the server.")
  commands.add("uninstall-ca", uninstall_ca, help="uninstall CA and all certs on the server.")

def install_ca(args):
  '''
  Apache installation

  '''
  return
  app.print_verbose("Install CA version: %d" % script_version)
  version_obj = version.Version("InstallCa", script_version)
  version_obj.check_executed()

  if os.path.exists('/etc/ssl/ca/private/ca.key'):
    app.print_verbose("CA is already installed")
  else:
    #making folders
    general.shell_exec("mkdir -p /etc/ssl/ca/private")
    general.shell_exec("mkdir -p /etc/ssl/certs")

    #creating certs
    os.chdir("/etc/ssl")
    general.shell_exec("openssl genrsa -out ca/private/ca.key 4096")
    general.shell_exec("openssl req -new -key ca/private/ca.key -out ca/ca.csr -subj '/O=syco/OU=System Console Project/CN=systemconsole.github.com'")
    general.shell_exec("openssl x509 -req -days 365 -in ca/ca.csr -signkey ca/private/ca.key -out ca/ca.crt ")

    #creating server certs
    general.shell_exec("openssl genrsa -out certs/www.webbserver.com.key 2048")
    general.shell_exec("openssl req -new -key certs/www.webbserver.com.key -out certs/www.webbserver.com.csr")
    general.shell_exec("openssl x509 -req -days 365 -in certs/www.webbserver.com.csr -signkey ca/private/ca.key -out certs/www.webbserver.com.crt ")

  version_obj.mark_executed()

def uninstall_ca(args):
  '''
  Remove ca and all certs in the ca

  '''
  return
  app.print_verbose("Uninstall CA")

  if (os.path.exists('/etc/ssl/ca/private/ca.key')):
    general.shell_exec("rm -rf /etc/ssl/")

  version_obj = version.Version("InstallCa", script_version)
  version_obj.mark_uninstalled()


