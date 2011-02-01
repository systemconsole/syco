#!/usr/bin/env python
'''
Application global wide helper functions.

Changelog:
  2011-02-01 - Daniel Lindh - Some minor refactoring and commenting.
  2011-01-29 - Daniel Lindh - Adding file header and comments
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel.lindh@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import ConfigParser
import os
import re
import socket
import sys
import time

import general
import passwordStore

#
#  Contains global functions and settings for the fosh app
#

# The version of the fosh script
version = "0.1"
parser = ''

# FOSH root folder.
FOSH_PATH = os.path.abspath(sys.path[0] + "/../")

# Scripts that should be availble in public repos.
FOSH_PUBLIC_PATH = os.path.abspath(FOSH_PATH + "/bin/public/")

# Scripts that should only be available in private repos.
FOSH_PRIVATE_PATH = os.path.abspath(FOSH_PATH + "/bin/private/")

# Etc (config) files.
FOSH_ETC_PATH = FOSH_PATH + "etc/"

# Files (rpm etc.) that should be installed by fosh, are temporary stored here.
INSTALL_DIR = "/tmp/install/"

# All passwords used by fosh are stored in this enrypted file.
PASSWORD_STORE_PATH = "/opt/fosh/etc/passwordstore"

# String codes affecting output to shell.
BOLD = "\033[1m"
RESET = "\033[0;0m"

# Global accessible object containing all install.cfg options.
config_file_name = FOSH_ETC_PATH + "install.cfg"
config = ConfigParser.RawConfigParser()
config.read(config_file_name)

# Options set from commandline are stored here.
class Options:

  # Set by -v and -q.
  verbose = 1

options = Options()

def print_error(message, verbose_level=1):
  '''
  Print bold error text to stdout, affected by the verbolse level.

  All error print to screen done by fosh should be done with this.

  '''
  print_verbose(message, verbose_level=verbose_level, caption=BOLD + "Error: " + RESET)

def print_verbose(message, verbose_level=1, caption="", new_line=True):
  '''
  Print a text to the stdout, affected by the verbose level.

  All print to screen done by fosh should be done with this.

  #TODO: The caption are not always written ok when using new_line=False, see example at the bottom 
  '''
  if (caption):
    caption += " "
  caption = time.strftime('%Y-%m-%d %H:%M:%S') + " - " + socket.gethostname() + " - " + caption

  messages = []
  if (not isinstance(message, tuple)):
    messages.append(message)
  else:
    messages = message

  # Output will look like
  # fo-tp-system: Caption This is a message
  for msg in messages:    
    if (len(str(msg)) > 0):
      msg = re.sub("[\n]", "\n" + caption, str(msg))

    if (options.verbose >= verbose_level):
      if (new_line):
        msg = caption + str(msg) + "\n"
      
      sys.stdout.write(msg)
      sys.stdout.flush()

def _get_password(service, user_name):
  '''
  Get a password from the password store.

  '''
  if (not get_password.password_store):
    get_password.password_store = passwordStore.PasswordStore(PASSWORD_STORE_PATH)
  return get_password.password_store.get_password(service, user_name)
_get_password.password_store = None

def get_root_password():
  '''The linux shell root password.'''
  return _get_password("linux", "root")

def get_root_password_hash():
  '''
  Openssl hash of the linux root password.

  '''
  root_password = get_root_password()
  hash_root_password = general.shell_exec_p("openssl passwd -1 -salt 'sa#Gnxw4' '" + root_password + "'")
  return hash_root_password

def get_svn_password():
  '''The svn password for user syscon_svn'''
  return _get_password("svn", "syscon_svn")

def get_glassfish_master_password():
  '''Used to sign keystore, never transfered over network.'''
  return _get_password("glassfish", "master")

def get_glassfish_admin_password():
  '''Login to asadmin or web admin console'''
  return _get_password("glassfish", "admin")

def get_mysql_root_password():
  '''The root password for the mysql service.'''
  return _get_password("mysql", "root")

def get_mysql_fp_integration_password():
  '''A user password for the mysql service, used by Farepayment'''
  return _get_password("mysql", "fp_integration")

def get_mysql_fp_stable_password():
  '''A user password for the mysql service, used by Farepayment'''
  return _get_password("mysql", "fp_stable")

def get_mysql_fp_qa_password():
  '''A user password for the mysql service, used by Farepayment'''
  return _get_password("mysql", "fp_qa")

def get_mysql_fp_production_password():
  '''A user password for the mysql service, used by Farepayment'''
  return _get_password("mysql", "fp_production")

def init_all_passwords():
  '''
  Ask the user for all passwords used by fosh, and add to passwordstore.

  '''
  get_root_password()
  get_svn_password()
  get_glassfish_master_password()
  get_glassfish_admin_password()
  get_mysql_root_password()
  get_mysql_fp_integration_password()
  get_mysql_fp_stable_password()
  get_mysql_fp_qa_password()
  get_mysql_fp_production_password()

def get_option(section, option):
  '''
  Get an option from the install.cfg file.

  '''
  if (config.has_section(section)):
    if (config.has_option(section, option)):
      return config.get(section, option)
    else:
      raise Exception("Can't find option '" + option + "' in section '" + section + "' in install.cfg")
  else:
    raise Exception("Can't find section '" + section + "' in install.cfg")

def get_mysql_primary_master():
  '''IP or hostname for primary mysql server.'''
  return get_ip(get_option("general", "mysql.primary_master"))

def get_mysql_secondary_master():
  '''IP or hostname for secondary mysql server.'''
  return get_ip(get_option("general", "mysql.secondary_master"))

def get_installation_server():
  '''The hostname of the installation server.'''
  return get_option("general", "installation_server")

def get_installation_server_ip():
  '''The ip of the installation server.'''
  return get_ip(get_installation_server())

def get_dns_resolvers():
  '''ip list of dns resolvers that are configured on all servers.'''
  return get_option("general", "dns_resolvers")

def get_ip(host_name):
  '''Get ip for a specific host, as it is defined in install.cfg'''
  return get_option(host_name, "server")

def get_mac(host_name):
  '''Get network mac address for a specific host, as it is defined in install.cfg'''
  return get_option(host_name, "mac")

def get_ram(host_name):
  '''Get the amount of ram in MB that are used for a specific kvm host, as it is defined in install.cfg.'''
  return get_option(host_name, "ram")

def get_cpu(host_name):
  '''Get the number of cores that are used for a specific kvm host, as it is defined in install.cfg'''
  return get_option(host_name, "cpu")

def get_disk_var(host_name):
  '''Get the size of the var partion in GB that are used for a specific kvm host, as it is defined in install.cfg'''
  return get_option(host_name, "disk_var")

def get_servers():
  '''A list of all servers that are defined in install.cfg.'''
  servers = config.sections()
  servers.remove("general")
  return servers

def get_commands(host_name):
  '''Get all commands that should be executed on a host'''
  options = []

  if (config.has_section(host_name)):
    for option, value in config.items(host_name):
      option = option.lower()
      if "command" in option:
        options.append([option, value])

  return sorted(options)

def get_guests(host_name):
  '''Get the hostname of all guests that should be installed on the kvm host name.'''
  guests = []

  if (config.has_section(host_name)):
    for option, value in config.items(host_name):
      if ("guest" in option):
        guests.append(value)

  return sorted(guests)


if (__name__ == "__main__"):
  print_error("This is a error.")
  print_verbose("This is some text")
  long_text = '''First line
New line

Another new line

last new line'''
  print_verbose(long_text, caption="fo-tp-vh01", new_line=False)
  print_verbose(", and some more text on the last line", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=False)
  print_verbose(".", caption="fo-tp-vh01", new_line=True)

