#!/usr/bin/env python
'''
Install of Snort

Snort in an NIDS that lissen on network interface.
and if network traffic matches rule in snort rules databas an alert in triggerd.

Snort is downloaded and bulid fron snort homepage.
Snortrules that contains all the rules nedded for snort to work are downloaded with key.

Workflow
- Download snort and daq
- Installing depenises
- Buildning daq and snort
- Installing snort and daq.
- Setting upp snort config and rules
- Making snort start at boot.
- Removing not needed rules from config.
- Enabling host relevant rules to snort.

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


import app
from general import x, download_file, md5checksum
import version
from scopen import scOpen


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-snort", install_snort, help="Install Snort.")
  commands.add("uninstall-snort", uninstall_snort, help="uninstall Snort.")






def install_snort(args):
  '''
  Install and setup snort in client.
  And conencts the snort loggs 
  '''
  snort_url="http://www.snort.org/downloads/1862"
  daq_url="http://www.snort.org/downloads/1850"

  snort_rule_url="wget http://www.snort.org/sub-rules/snortrules-snapshot-2931.tar.gz/6f1a1622979dec80485a8d8a2acc7b0c8149ddc2"
  

  snort_md5="b2102605a7ca023ad6a2429821061c29"
  daq_md5="bc204ea09165b4ecbb1bb49c7c1a2ad4"

  #x('yum install gcc flex bison zlib zlib-devel libpcap libpcap-devel pcre pcre-devel libdnet libdnet-devel tcpdump -y')
  
  download_make(snort_url, snort_md5)
  download_make(daq_url, daq_md5)

  #Remeoving content /etc/snort-rules
  x("rm -rf /etc/snort/*")

  #Setting up snort config and rules DISABLED 
  #download_file(snort_rule_url,"snort-rules.tar")
  #x("mv "+app.INSTALL_DIR+"snort-rules.tar /etc/snort")
  #x("tar -C /etc/snort -zxvf /etc/snort/snort-rules.tar")
  
  
  x("\cp -f /opt/syco/var/snort/snortrules-snapshot.tar.gz /etc/snort")
  x("tar -C /etc/snort -zxvf /etc/snort/snortrules-snapshot.tar.gz")
  x("rm -rf /etc/snort/snort-rules.tar")


  #Setting upp start and syscong scripts.
  x('\cp -f /opt/syco/var/snort/snort_init.d /etc/init.d/snort')
  x('\cp -f /opt/syco/var/snort/snort_sysconfig /etc/sysconfig/snort')  
  #Setting upp extra config

  x("useradd snort -d /var/log/snort -s /sbin/nologin -c SNORT_IDS")
  x("chown snort:snort /etc/snort/ -R")

  #Setting upp inid. start up
  x("chmod 700 /etc/init.d/snort")

  #enabling at start up
  x("chkconfig --add snort")

  #snort bin
  x("ln -s /usr/local/bin/snort /usr/bin/snort")
  x("ln -s /usr/local/bin/snort /usr/sbin/snort")
  x("chmod 700 /usr/bin/snort")
  x("chmod 700 /usr/sbin/snort")

  #sysconfig
  x("chown snort:snort /etc/sysconfig/snort")
  x("chmod 700 /etc/sysconfig/snort")

  #Making log folders
  x("mkdir /var/log/snort/")
  x("chmod 700 /var/log/snort/")
  x("chown snort:snort /var/log/snort/")


  x("mkdir -p /usr/local/lib/snort_dynamicrules")
  x("chown snort:snort /usr/local/lib/snort_dynamic* -R")
  x("chown snort:snort /usr/local/lib/snort* -R")
  x("chmod -R 700 /usr/local/lib/snort* ")

  
  #Coping in snort syco rules to config file
  x("\cp -f /opt/syco/var/snort/snort.conf /etc/snort/etc")
  x("echo '#whitlist' >/etc/snort/rules/black_list.rules")
  x("echo '#whitlist' >/etc/snort/rules/white_list.rules")


  x("/etc/init.d/snort restart")


def download_make(url,md5):
  '''
  Takes an url and download and hash.
  Download the file checks md5 and then download and build the package. 
  '''


  download_file(url,"download.tar")
  compile_dir=app.INSTALL_DIR+"build" 

  if md5checksum(app.INSTALL_DIR+"download.tar") != md5:
    raise Exception("Mmd5 Checksum dont match") 

  x("mkdir "+app.INSTALL_DIR+"download")
  x("tar -C "+app.INSTALL_DIR+"download -zxf "+app.INSTALL_DIR+"download.tar")
  x("mv "+app.INSTALL_DIR+"download/* "+app.INSTALL_DIR+"build")
  x("chown -R root:root %s" % compile_dir)
  x("./configure --enable-debug --enable-debug-msgs", cwd=compile_dir)
  x("make", cwd=compile_dir)
  x("make install", cwd=compile_dir)
  x("rm -rf "+app.INSTALL_DIR+"build")
  x("rm -rf "+app.INSTALL_DIR+"download")
  x("rm -rf "+app.INSTALL_DIR+"download.tar")




def uninstall_snort(args):
  '''
  uninstall snort
  '''
  print "Removing snort"
