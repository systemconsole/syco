#!/usr/bin/env python
'''
Network related functions.

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

import socket, os
import fcntl, struct

def get_interface_ip(ifname):  
  '''
  Get ip from a specific interface.
  
  Example:
  ip = get_interface_ip("eth0")
  
  '''
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
  return socket.inet_ntoa(fcntl.ioctl(    
    s.fileno(),    
    0x8915,  # SIOCGIFADDR    
    struct.pack('256s', ifname[:15])    
  )[20:24])

# Cache variable for lan_ip
lan_ip = ""

def get_lan_ip():
  '''
  Get one of the external ips on the computer.
  
  Prioritize ips from interface in the following orders
  "eth0","eth1","eth2","wlan0","wlan1","wifi0","ath0","ath1","ppp0"
  
  '''
  global lan_ip
  if (lan_ip==""):
    lan_ip = socket.gethostbyname(socket.gethostname())
    
    if lan_ip.startswith("127.") and os.name != "nt":
      interfaces = ["eth0","eth1","eth2","wlan0","wlan1","wifi0","ath0","ath1","ppp0"]
      
      for ifname in interfaces:      
        try:      
          lan_ip = get_interface_ip(ifname)      
          break;
        
        except IOError:      
          pass
      
  return lan_ip
