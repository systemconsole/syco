#! /usr/bin/env python


import ConfigParser
import os
import app
import general
import re

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the fosh.py shell script. 
  
  '''
  commands.add("remove-dns",   remove_dns,  help="Remove DNS server.")



 
def remove_dns(args):
  '''
  Remove DNS server
  
  '''
 # self.prop.init_properties(args[1])
 # version_obj=version.Version("installDns" + self.prop.environment, self.SCRIPT_VERSION)
 # version_obj.check_executed()

  if os.path.exists('/var/named/chroot/etc/named.conf'):

    app.print_verbose("DNS Server is Installed REMOVING")

  else:

    app.print_verbose("DNS Server is Not installed")