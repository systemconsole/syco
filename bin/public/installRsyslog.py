#!/usr/bin/env python
'''
Install of rsyslog client to connect to rsyslog server

Install rsyslog client and set up tls to server on tcp port 514 and unecrypted loggnin on udp 514.

[Logging to]
Loggs are the saved local on server
And sent to rsyslog server to store on strukture in /var/log/remote/year/month/day/servername and mysql server

[Newcerts]
Clients will collect their certs from the rsyslog server

[Configfiles]
rsyslog.d config files are located in syco/var/rsyslog/ folder
template used for generating certs are located in /syco/var/rsyslog/template.ca and templat.client


[More reading]
http://www.rsyslog.com/doc/rsyslog_tls.html
http://www.rsyslog.com/doc/rsyslog_mysql.html



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
import config
from ssh import scp_from
from config import get_servers, host
import socket
import net



import app
from general import x
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-rsyslog", install_rsyslog, help="Install rsyslog client on the server.")
  commands.add("uninstall-rsyslog", uninstall_rsyslog, help="uninstall rsyslog client and all certs on the server.")




def install_rsyslog(args):
  '''
  Install rsyslog client the server
  and set upp configfiles to use rsyslog server and collect server tls cert

  '''
  hostname = socket.gethostname()
  x("yum install rsyslog rsyslog-gnutls -y")
  x("chkconfig --add rsyslog")
  x("chkconfig rsyslog on")

  #Getting loggservers server
  logserver =config.general.get_log_server_hostname()
  logserver2 =config.general.get_log_server_hostname2()

  x("\cp -f /opt/syco/var/rsyslog/rsyslog.conf /tmp/rsyslog.conf" )
  x("sed -i 's/SERVERNAME/"+net.get_hostname()+"."+config.general.get_resolv_domain()+"/g' /tmp/rsyslog.conf")
  x("sed -i 's/DOMAIN/"+config.general.get_resolv_domain()+"/g' /tmp/rsyslog.conf")
  x("sed -i 's/MASTER/"+logserver+"/g' /tmp/rsyslog.conf")
  x("sed -i 's/SLAVE/"+logserver2+"/g' /tmp/rsyslog.conf")

  x("\cp -f /tmp/rsyslog.conf /etc/rsyslog.conf" )


  #coping certs for tls from rsyslog server
  x("mkdir /etc/pki/rsyslog")
  scp_from(logserver,"/etc/pki/rsyslog/%s*" % net.get_hostname(),"/etc/pki/rsyslog")
  scp_from(logserver,"/etc/pki/rsyslog/ca.pem","/etc/pki/rsyslog")
  
  #Restaring rsyslog
  x("/etc/init.d/rsyslog restart")



def uninstall_rsyslog(args):
  '''
  Unistall rsyslog and erase all files
  '''
  x("yum erase rsyslog -y")
  x("rm -rf /etc/pki/rsyslog")
