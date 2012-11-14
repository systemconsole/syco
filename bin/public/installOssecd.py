#!/usr/bin/env python
'''
Install of OSSEC Server 

Ossec is and host based intrusion system. It monitors the system logs and 
triggers alert to logg messages ore changes made to the system like file changes.

The OSSEC server can be and standalon installtion ore have mulipel OSSEC agents connected to it.
OSSEC clients are connecte over udb port 1514 and are using keys to auth to the OSSEC server.


install-ossecd installs ossec server by 

*Coping the OSSEC build server to temp
*Coping in the prefilld ossec install file to the OSSEC build config
*Making the OSSEC installation by triggning make & make install
*Setting upp servers i install.cfg as klients and generating keys for server
*Coping keys to sepperta file for client to fetch
*Setting upp OSSEC to log to syslog server
*Starting ossec-remote 
*Staring OSSEC

[Location]
OSSEC are installed in /var/ossec folders.

[Change Installation]
To make changes to the installtion se the file

syco/var/ossec/osseconf/preloaded-vars-server.conf

[Change OSSEC conf]
To make changes to the OSSEC server edit the file

syco/var/ossec/osseconf/ossec_server.conf


[Set upp custom rules]
To make changes and add custom rules edit the file

syco/var/ossec/osseconf/local_rules.xml


[more reading]
http://www.ossec.net/

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
import iptables
from config import get_servers, host


import app
from general import x, download_file, md5checksum
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-ossecd", install_ossecd, help="Install Ossec Server on the server.")
  commands.add("uninstall-ossecd", uninstall_ossecd, help="uninstall Ossec Server and all certs on the server.")

def install_ossecd(args):
  '''
  Install OSSEC server in the server

  '''
  #OSSEC DOWNLOAD URL
  ossec_download = "http://www.ossec.net/files/ossec-hids-2.6.tar.gz"
  ossec_md5 = "f4140ecf25724b8e6bdcaceaf735138a"


  #Downloading and md5 checking
  x('yum install gcc make perl-Time-HiRes -y')
  download_file(ossec_download, "ossec-hids.tar.gz")
  if md5checksum(app.INSTALL_DIR+"ossec-hids.tar.gz") != ossec_md5:
    raise Exception("Mmd5 Checksum dont match")

  #Preparing OSSEC for building
  x("tar -C "+app.INSTALL_DIR+" -zxf "+app.INSTALL_DIR+"ossec-hids.tar.gz  ")
  x("mv "+app.INSTALL_DIR+"ossec-hids-* "+app.INSTALL_DIR+"ossecbuild")

  #Coping in ossec settings before build
  x('\cp -f /opt/syco/var/ossec/osseconf/preloaded-vars-server.conf '+app.INSTALL_DIR+'ossecbuild/etc/preloaded-vars.conf')
  
  #Building OSSEC
  x(app.INSTALL_DIR+'ossecbuild/install.sh')
  
  #Generating keys for ossec all klients
  for server in get_servers():

    x(app.INSTALL_DIR+'/ossecbuild/contrib/ossec-batch-manager.pl -a -n '+server+'.'+config.general.get_resolv_domain()+' -p '+config.host(server).get_front_ip())
    x("grep "+server+"."+config.general.get_resolv_domain()+" /var/ossec/etc/client.keys > /var/ossec/etc/"+server+"."+config.general.get_resolv_domain()+"_client.keys")


  #Setting upp server config and local rules from syco
  x('\cp -f /opt/syco/var/ossec/osseconf/ossec_server.conf /var/ossec/etc/ossec.conf')
  x('\cp -f /opt/syco/var/ossec/osseconf/local_rules.xml /var/ossec/rules/local_rules.xml')
  x('chown root:ossec  /var/ossec/rules/local_rules.xml')
  x('chmod 550  /var/ossec/rules/local_rules.xml')
  x('chown root:ossec  /var/ossec/etc/ossec.conf')
  x('chmod 550  /var/ossec/etc/client.keys')
  x('chown ossec:ossec  /var/ossec/etc/client.keys')

  #Enabling syslog logging
  x('/var/ossec/bin/ossec-control enable client-syslog')

  #Restaring OSSEC server
  x('/var/ossec/bin/ossec-control restart')
  x('/var/ossec/bin/ossec-remoted start')


  # Let clients connect to the server through the firewall. This is done after
  # everything else is done, so we are sure that the server is secure before
  # letting somebody in.
  iptables.add_ossec_chain()
  iptables.save()

  #Cleaning upp install
  x('yum remove gcc make perl-Time-HiRes -y')

def uninstall_ossecd(args):
  '''
  Remove OSSECD server from the server

  '''
  #Stoping OSSEC
  x('/var/ossec/bin/ossec-control stop')
  x('/var/ossec/bin/ossec-remoted stop')
  
  #Removning folders
  x('rm -rf /var/log/ossec')




