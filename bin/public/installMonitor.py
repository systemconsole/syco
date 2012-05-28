#! /usr/bin/env python
'''
package is an script for installing nagis nrpe server on the host.
The nrpe server uses the nagios plugins package and runs the check kommands .

The script does 

Sett up syslog settings from Capter 6 CIS redhar benchmark


__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "syco@cybercow.se


'''

import ConfigParser
import os
import time
import stat
import shutil
import traceback
from general import x
import config
import sys
import app
import general
import version
import iptables

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the fosh.py shell script.

  '''
  commands.add("install-monitor",   install_monitor,  help="Install Nagios and munin node server on the server.")


def install_monitor(args):
  '''
  Monitor installation
  
  This script install nagios-plugins-all and nrpe server to the host.
  the host is then setup to allow cennections from the monitor server nand to reply 
  back results to the monitor server.

  Install munin-node to accept muninserver connections.

  '''

  
  #Installting nagios plugins and nrpe server
  general.shell_exec("yum install nagios-plugins-all nrpe munin-node -y")

  #Setting upp nrpe config for 
  #-Accepting connections from m#onitor-tp.*
  #-Adding to use fareoffice nrpe commands
  #-Removing all commands in nrpe.conf file
  general.set_config_property("/etc/nagios/nrpe.cfg","^allowed_hosts=.*","allowed_hosts="+config.general.get_monitor_server())
  general.set_config_property("/etc/nagios/nrpe.cfg","^[\#]?command.*","#command")
  general.set_config_property("/etc/nagios/nrpe.cfg","^dont_blame_nrpe=.*","dont_blame_nrpe=1")

  munin_ip = config.general.get_monitor_server().split(".");
  

  general.set_config_property("/etc/munin/munin-node.conf","^allow.*","allow "+munin_ip[0]+"\."+munin_ip[1]+"\."+munin_ip[2]+"\."+munin_ip[3]+"")
  x("rm /etc/nrpe.d/nrpe_fareoffice.cfg")
  x("cp /opt/syco/var/monitor/nrpe_fareoffice.cfg /etc/nrpe.d/nrpe_fareoffice.cfg")

  
  # Openning ports in iptabled for accepting connections from
  # monitor server.
  # Opening port 4949 munin and 5666 nrpe
  iptables.add_monitor_chain()

  #Restaring services
  general.shell_exec('/etc/init.d/nrpe restart')
  general.shell_exec('/etc/init.d/munin-node restart')
