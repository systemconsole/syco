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
from config import get_servers, host


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
  commands.add("install-ossecd", install_ossecd, help="Install Ossec Server on the server.")
  commands.add("uninstall-ossecd", uninstall_ossecd, help="uninstall Ossec Server and all certs on the server.")

def install_ossecd(args):
  '''
  Install OSSEC server in the server

  '''
  #OSSEC DOWNLOAD URL
  ossec_download = "http://www.ossec.net/files/ossec-hids-2.6.tar.gz"


  #Installing OSSEC
  x('yum install gcc make perl-Time-HiRes')
  x("wget -P /tmp/ {0}".format(ossec_download))
  x("tar -C /tmp -zxf /tmp/ossec-hids*  ")
  x("rm -rf /tmp/ossec-hids*.tar.gz")
  x("mv /tmp/ossec-hids* /tmp/ossecbuild")



  x('\cp -f /opt/syco/var/ossec/osseconf/preloaded-vars-server.conf /tmp/ossecbuild/etc/preloaded-vars.conf')
  x('/tmp/ossecbuild/install.sh')
  
  #Generating keys for ossec all klients to work
  for server in get_servers():

    x("/tmp/ossecbuild/contrib/ossec-batch-manager.pl -a -n {0}.fareoffice.com -p {1}".format(server,config.host(server).get_back_ip()))
    x("grep {0}.fareoffice.com /var/ossec/etc/client.keys > /var/ossec/etc/{0}.fareoffice.com_client.keys".format(server))


  #Setting upp server config and local rules from syco
  ('\cp -f /opt/syco/var/ossec/osseconf/ossec_server.conf /var/ossec/etc/ossec.conf')
  x('\cp -f /opt/syco/var/ossec/osseconf/local_rules.xml /var/ossec/rules/local_rules.xml')
  x('chown root:ossec  /var/ossec/rules/local_rules.xml')
  x('chmod 550  /var/ossec/rules/local_rules.xml')
  x('chown root:ossec  /var/ossec/etc/ossec.conf')

  #Enabling syslog logging
  x('/var/ossec/bin/ossec-control enable client-syslog')

  #Restaring OSSEC server
  x('/var/ossec/bin/ossec-control restart')
  x('/var/ossec/bin/ossec-remoted start')

  #Cleaning upp install
  x('rm -rf /tmp/ossecbuild')
  x('yum remove gcc make perl-Time-HiRes')

def uninstall_ossecd(args):
  '''
  Remove OSSECD server from the server

  '''
  #Stoping OSSEC
  x('/var/ossec/bin/ossec-control stop')
  x('/var/ossec/bin/ossec-remoted stop')
  
  #Removning folders
  x('rm -rf /var/log/ossec')




