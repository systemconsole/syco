#!/usr/bin/env python
'''
Application global wide helper functions.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import re
import socket
import sys
import time
import subprocess

from constant import *

# Need to be after all constants.
import options
options = options.Options()

import config
config.load(SYCO_ETC_PATH, SYCO_USR_PATH)



import install

# Syco uses packages from the EPEL repo.
install.epel_repo()

# Required yum package.
install.package("gnupg2")

import passwordStore

def print_error(message, verbose_level=1):
  '''
  Print bold error text to stdout, affected by the verbolse level.

  All error print to screen done by syco should be done with this.

  '''
  print_verbose(message, verbose_level=verbose_level, caption=BOLD + "Error: " + RESET)

def print_verbose(message, verbose_level=1, caption=None, new_line=True, enable_caption=True):
  '''
  Print a text to the stdout, affected by the verbose level.

  All print to screen done by syco should be done with this.

  #TODO: The caption are not always written ok when using new_line=False, see example at the bottom.

  '''
  if (caption):
    caption += " "
  else:
    caption=""
  caption = time.strftime('%Y-%m-%d %H:%M:%S') + " - " + socket.gethostname() + " - " + caption

  messages = []
  if (not isinstance(message, tuple)):
    messages.append(message)
  else:
    messages = message

  # Output will look like
  # syco-system: Caption This is a message
  for msg in messages:
    if (len(str(msg)) > 0):
      msg = re.sub("[\n]", "\n" + caption, str(msg))

    if (options.verbose >= verbose_level):
      msg = str(msg)
      if (enable_caption):
        msg = caption + msg

      if (new_line):
        msg += "\n"

      sys.stdout.write(msg)
      sys.stdout.flush()

def _get_password_store():
  '''
  Get a password store object.

  '''
  if (not _get_password_store.password_store):
    _get_password_store.password_store = passwordStore.PasswordStore(PASSWORD_STORE_PATH)

  return _get_password_store.password_store

_get_password_store.password_store = None

def _get_password(service, user_name):
  '''
  Get a password from the password store.

  '''
  password = _get_password_store().get_password(service, user_name)
  _get_password_store().save_password_file()
  return password

def get_master_password():
  '''
  Get a password from the password store.

  '''
  password = _get_password_store().get_master_password()
  _get_password_store().save_password_file()
  return password

def get_root_password():
  '''The linux shell root password.'''
  return _get_password("linux", "root")

def get_root_password_hash():
  '''
  Openssl hash of the linux root password.

  '''
  root_password = get_root_password()
  p = subprocess.Popen("openssl passwd -1 -salt 'sa#Gnxw4' '" + root_password + "'", stdout=subprocess.PIPE, shell=True)
  hash_root_password, stderr = p.communicate()
  return str(hash_root_password)

def get_user_password(username):
  '''The linux shell password for a specific user.'''
  return _get_password("linux", username)

def get_ca_password():
  '''The password used when creating CA certificates'''
  return get_root_password()

def get_svn_password():
  '''The svn password for user syscon_svn'''
  return _get_password("svn", "syscon")

def get_glassfish_master_password():
  '''Used to sign keystore, never transfered over network.'''
  return _get_password("glassfish", "master")

def get_glassfish_admin_password():
  '''Login to asadmin or web admin console'''
  return _get_password("glassfish", "admin")

def get_mysql_root_password():
  '''The root password for the mysql service.'''
  return _get_password("mysql", "root")

def get_mysql_password(env):
  '''A user password for the mysql service.'''
  return _get_password("mysql", env)

def get_mysql_integration_password():
  '''A user password for the mysql service.'''
  return _get_password("mysql", "integration")

def get_mysql_stable_password():
  '''A user password for the mysql service.'''
  return _get_password("mysql", "stable")

def get_mysql_uat_password():
  '''A user password for the mysql service.'''
  return _get_password("mysql", "uat")

def get_mysql_production_password():
  '''A user password for the mysql service.'''
  return _get_password("mysql", "production")

def init_mysql_passwords():
  get_mysql_root_password()
  get_mysql_integration_password()
  get_mysql_stable_password()
  get_mysql_uat_password()
  get_mysql_production_password()

def init_all_passwords():
  '''
  Ask the user for all passwords used by syco, and add to passwordstore.

  '''
  get_root_password()
  get_svn_password()
  get_glassfish_master_password()
  get_glassfish_admin_password()
  get_user_password("glassfish")
  init_mysql_passwords()

def get_mysql_primary_master():
  '''IP or hostname for primary mysql server.'''
  return config.general.get_mysql_primary_master_ip()

def get_mysql_secondary_master():
  '''IP or hostname for secondary mysql server.'''
  return config.general.get_mysql_secondary_master_ip()

def get_gateway_server_ip():
  '''The ip of the network gateway.'''
  return config.general.get_back_gateway_ip()

def get_installation_server():
  '''The hostname of the installation server.'''
  return config.general.get_installation_server()

def get_installation_server_ip():
  '''The ip of the installation server.'''
  return config.general.get_installation_server_ip()

def get_cert_server():
  '''The hostname of the cert server.'''
  return config.general.get_cert_server()

def get_cert_server_ip():
  '''The ip of the cert server.'''
  return config.general.get_cert_server_ip()

def get_servers():
  '''A list of all servers that are defined in install.cfg.'''
  return config.get_servers()

def get_hosts():
  return config.get_hosts()

if (__name__ == "__main__"):
  print_error("This is a error.")
  print_verbose("This is some text")
  long_text = '''First line
New line

Another new line

last new line'''
  print_verbose(long_text, caption="syco-vh01", new_line=False)
  print_verbose(", and some more text on the last line", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=True, enable_caption=False)

