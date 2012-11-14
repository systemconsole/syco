#!/usr/bin/env python
'''
Install of OSSEC AGENT / CLIENT 

Ossec is and host based intrusion system. It monitors the system logs and 
triggers alert to logg messages ore changes made to the system like file changes.

The OSSEC AGENT is to e installed on an server and then connected to the OSSEC Server.
OSSEC AGENT fetchs keys from the OSSEC SERVER to be able to verify to the server.

*important*
The hostname of the client MUST BE THE same as in the install.cfg.
Server called "webbserver" in install.cfg must have hostname webbserver.domain.se as hostname



install-ossecd installs ossec server by 

*Coping the OSSEC build server to temp
*Coping in the prefilld ossec install file to the OSSEC build config
*Making the OSSEC installation by triggning make & make install
*Fetching keys from OSSEC SERVER
*Staring OSSEC

[Location]
OSSEC are installed in /var/ossec folders.

[Change Installation]
To make changes to the installtion se the file

syco/var/ossec/osseconf/preloaded-vars-agent.conf

[Change OSSEC conf]
To make changes to the OSSEC server edit the file

syco/var/ossec/osseconf/ossec_agent.conf


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
from config import get_servers, host
from ssh import scp_from
import socket
import iptables


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
  commands.add("install-ossec", install_ossec, help="Install Ossec Client.")
  commands.add("uninstall-ossec", uninstall_ossec, help="uninstall Ossec Client.")

def install_ossec(args):
  '''
  Install OSSEC Client in the server

  '''


  #OSSEC DOWNLOAD URL
  ossec_download = "http://www.ossec.net/files/ossec-hids-2.6.tar.gz"
  ossec_md5 = "f4140ecf25724b8e6bdcaceaf735138a"
  #Getting ossec server
  ossecserver =config.general.get_ossec_server_ip()
  hostname = socket.gethostname()

  #Downloading and md5 checking
  x('yum install gcc make perl-Time-HiRes -y')
  download_file(ossec_download, "ossec-hids.tar.gz")
  if md5checksum(app.INSTALL_DIR+"ossec-hids.tar.gz") != ossec_md5:
    raise Exception("Mmd5 Checksum dont match")

  #Preraring to build Ossec
  x("tar -C "+app.INSTALL_DIR+" -zxf "+app.INSTALL_DIR+"ossec-hids.tar.gz  ")
  x("mv "+app.INSTALL_DIR+"ossec-hids-* "+app.INSTALL_DIR+"ossecbuild")

  x('\cp -f /opt/syco/var/ossec/osseconf/preloaded-vars-agent.conf '+app.INSTALL_DIR+'ossecbuild/etc/preloaded-vars.conf')

  #Setting ossec server ip
  x("sed -i 's/${OSSECSERVER}/"+ossecserver+"/g' "+app.INSTALL_DIR+"ossecbuild/etc/preloaded-vars.conf")
  
  #Start building OSSEC
  x(app.INSTALL_DIR+'ossecbuild/install.sh')

  #Getting OOSEC clinet key from OSSEC server.
  scp_from(ossecserver,"/var/ossec/etc/"+hostname+"_client.keys","/var/ossec/etc/client.keys")
  x('chown root:ossec  /var/ossec/etc/client.keys')

  #Setting upp client config from syco
  x('\cp -f /opt/syco/var/ossec/osseconf/ossec_agent.conf /var/ossec/etc/ossec.conf')
  x("sed -i 's/${OSSECSERVER}/"+ossecserver+"/g' /var/ossec/etc/ossec.conf")
  x('chown root:ossec  /var/ossec/etc/ossec.conf')
  x('chmod 550  /var/ossec/etc/client.keys')
  x('chown ossec:ossec  /var/ossec/etc/client.keys')

  #Restaring OSSEC client
  x('/var/ossec/bin/ossec-control restart')

  #Adding iptables rules 
  iptables.add_ossec_chain()
  iptables.save()

def uninstall_ossec(args):
  '''
  Remove OSSECD Client from the server

  '''
  #Stoping OSSEC client
  x('/var/ossec/bin/ossec-control stop')

  #Remove folders
  x('rm -rf /var/ossec')