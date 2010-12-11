#! /usr/bin/env python

import app, general

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("iptables-clear", iptables_clear, help="Clear all rules from iptables.")
  
def iptables_clear(args):
  '''
  
  '''
  app.print_verbose("Clear all iptables rules")
  # reset the default policies in the filter table.
  iptables("-P INPUT ACCEPT")
  iptables("-P FORWARD ACCEPT")
  iptables("-P OUTPUT ACCEPT")
  
  # reset the default policies in the nat table.
  iptables("-t nat -P PREROUTING ACCEPT")
  iptables("-t nat -P POSTROUTING ACCEPT")
  iptables("-t nat -P OUTPUT ACCEPT")
  
  # reset the default policies in the mangle table.
  iptables("-t mangle -P PREROUTING ACCEPT")
  iptables("-t mangle -P POSTROUTING ACCEPT")
  iptables("-t mangle -P INPUT ACCEPT")
  iptables("-t mangle -P OUTPUT ACCEPT")
  iptables("-t mangle -P FORWARD ACCEPT")
  
  # Flush all chains
  iptables("-F -t filter")
  iptables("-F -t nat")
  iptables("-F -t mangle")
  
  # Delete all user-defined chains
  iptables("-X -t filter")
  iptables("-X -t nat")
  iptables("-X -t mangle")
  
  # Zero all counters
  iptables("-Z -t filter")
  iptables("-Z -t nat")
  iptables("-Z -t mangle")
  
def iptables(args):
  general.shell_exec("/sbin/iptables " + args)