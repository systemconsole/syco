#! /usr/bin/env python

import socket, os
import fcntl, struct

def get_interface_ip(ifname):  
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
  return socket.inet_ntoa(fcntl.ioctl(    
    s.fileno(),    
    0x8915,  # SIOCGIFADDR    
    struct.pack('256s', ifname[:15])    
  )[20:24])

# Cache variable for lan_ip
lan_ip=""
def get_lan_ip():
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
