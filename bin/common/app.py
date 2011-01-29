#!/usr/bin/env python
'''
Application global wide helper functions.

Changelog:
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

import sys, ConfigParser, os, re, socket, getpass
import passwordStore

# Constants
#
BOLD="\033[1m"
RESET="\033[0;0m"

# The folder where files (rpm etc.) that should be installed, are stored.
INSTALL_DIR="/tmp/install/"

#
#  Contains global functions and settings for the fosh app
#

class Options:
  verbose=1
  
options = Options()

# The version of the fosh script
version="0.1"
parser=''

# Root password for linux shell.
root_password = None

PASSWORD_STORE_PATH = "/opt/fosh/etc/passwordstore"

# 
FOSH_PATH=os.path.abspath(sys.path[0] + "/../") 
FOSH_PUBLIC_PATH=os.path.abspath(FOSH_PATH + "/bin/public/") 
FOSH_PRIVATE_PATH=os.path.abspath(FOSH_PATH + "/bin/private/") 

fosh_path=os.path.abspath(sys.path[0] + "/../") 
config_file_name=fosh_path + "/etc/install.cfg"
config = ConfigParser.RawConfigParser()
config.read(config_file_name)

def print_error(message, verbose_level=1):
  print_verbose(message, verbose_level=verbose_level, caption=BOLD + "Error: " + RESET)
    
def print_info(message):
  print_verbose(message, caption="Info: ") 
    
def print_verbose(message, verbose_level = 1, caption="", new_line=True):
  global options

  messages = []
  if (not isinstance(message, tuple)):
    messages.append(message)
  else:
    messages = message
      
  for msg in messages:    
    host=socket.gethostname() + ": "
    if (len(str(msg))>0):
      msg=re.sub("[\n]", "\n" + host + caption, str(msg))    
  
    if (options.verbose >= verbose_level):    
      if (new_line):
        sys.stdout.write(host + caption + msg + "\n")
      else:
        sys.stdout.write(msg)
        
    sys.stdout.flush()

def get_option(section, option):
  if (config.has_section(section)):
    if (config.has_option(section, option)):
      return config.get(section, option)  
    else:      
      raise Exception("Can't find option '" + option + "' in section '" + section + "' in install.cfg")
  else:
    raise Exception("Can't find section '" + section + "' in install.cfg")

def get_password(service, user_name):
  '''
  Get password from the password store.
  
  '''
  if (not get_password.password_store):
    print "create password store"
    get_password.password_store=passwordStore.PasswordStore(PASSWORD_STORE_PATH)
  return get_password.password_store.get_password(service, user_name)
get_password.password_store=None
  
def get_root_password():
  '''
  Ask the user to enter the linux shell root password.
  
  TODO: Verify that it's the right password, raise Exception otherwise.
  
  '''
  global root_password
  
  while(root_password==""):
    root_password=getpass.getpass("Enter root password: ")
  return root_password

def get_root_password_hash():
  return get_option("general", "root_password")

def get_mysql_password():
  return get_option("general", "mysql.password")

def get_mysql_primary_master():
  return get_ip(get_option("general", "mysql.primary_master"))

def get_mysql_secondary_master():
  return get_ip(get_option("general", "mysql.secondary_master"))
  
def get_installation_server():
  return get_option("general", "installation_server")

def get_installation_server_ip():
  return get_ip(get_installation_server())

def get_dns_resolvers():
  return get_option("general", "dns_resolvers")
    
def get_ip(host_name):
  return get_option(host_name, "server")

def get_mac(host_name):
  return get_option(host_name, "mac")

def get_ram(host_name):
  return get_option(host_name, "ram")

def get_cpu(host_name):
  return get_option(host_name, "cpu")

def get_disk_var(host_name):
  return get_option(host_name, "disk_var")

def get_servers():
  global config
  servers=config.sections()
  servers.remove("general")
  return servers
  
def get_commands(host_name):
  options = []
  
  if (config.has_section(host_name)):
    for option, value in config.items(host_name):
      option=option.lower()
      if "command" in option:
        options.append([option, value])

  return sorted(options)
  
def get_guests(host_name):
  guests = []
  
  if (config.has_section(host_name)):
    for option, value in config.items(host_name):
      if ("guest" in option):
        guests.append(value)

  return sorted(guests)