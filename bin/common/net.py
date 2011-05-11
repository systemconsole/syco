#!/usr/bin/env python
'''
Network related functions.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
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
    try:
      lan_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
      pass

    if lan_ip == "" or (lan_ip.startswith("127.") and os.name != "nt"):
      interfaces = ["eth0","eth1","eth2","wlan0","wlan1","wifi0","ath0","ath1","ppp0"]

      for ifname in interfaces:
        try:
          lan_ip = get_interface_ip(ifname)
          break;

        except IOError:
          pass

  return lan_ip

def reverse_ip(str):
	'''Reverse an ip from 1.2.3.4 to 4.3.2.1'''
	reverse_str=""
	for num in str.split("."):
		if (reverse_str):
			reverse_str = "." + reverse_str
		reverse_str = num + reverse_str
	return reverse_str

def get_ip_class_c(ip):
  '''Get a class c net from an ip. 1.2.3.4 will return 1.2.3'''
  new_ip = ""
  split_ip = ip.split(".")
  for i in range(3):
		if (new_ip):
			new_ip += "."
		new_ip = new_ip + split_ip[i]

  return new_ip

if (__name__ == "__main__"):
  print get_lan_ip()
  print get_interface_ip("eth0")
