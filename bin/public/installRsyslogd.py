#!/usr/bin/env python
'''
Install of rsyslog server with mysql backend

Install rsyslog server and set up tls server on tcp port 514 and unecrypted loggnin on udp 514.

[Logging to]
Loggs are the saved to an mysql database Syslog.
And to files strukture in /var/log/remote/year/month/day/servername

[Newcerts]
installation can generat certs for rsyslog clinet if run with the newcerts arguments.
Certs are saved in /etc/pki/rsyslog folder.

Clients can then collect their certs from that location.

[Configfiles]
rsyslog.d config files are located in syco/var/rsyslog/ folder
template used for generating certs are located in /syco/var/rsyslog/template.ca and templat.server


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
from installMysql import install_mysql
from config import get_servers, host
import socket



import app
from general import x
from general import generate_password
import general
import version
import net

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 2

def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-rsyslogd", install_rsyslogd, help="Install Rsyslog server")
  commands.add("uninstall-rsyslogd", uninstall_rsyslogd, help="uninstall rsyslog server and all certs on the server.")
  commands.add("install-rsyslogd-newcerts", rsyslog_newcerts, help="Generats new cert for rsyslogd")

def install_rsyslogd(args):
  '''
  Install rsyslog serverin the server

  '''
  #Setting upp syco dependis
  args=["","1","2G"]
  print args

  #install_mysql(args)



  # Installing packages
  x("yum install rsyslog rsyslog-gnutls rsyslog-mysql gnutls-utils -y")

  #Making them start at boot
  x("chkconfig --add rsyslog")
  x("chkconfig --add mysqld")
  x("chkconfig rsyslog on")
  x("chkconfig mysqld on")

  #Getting argument from command line
  #master = setting upp master server
  #slave = setting upp slave server


  #Generation new certs if no certs exsists
  if not os.path.exists('/etc/pki/rsyslog/ca.pem'):
    rsyslog_newcerts()

  #Setting upp install dirs
  general.create_install_dir()

  #Coping config files
  x("\cp -f /opt/syco/var/rsyslog/initdb.sql "+app.INSTALL_DIR+"initdb.sql")
  x("\cp -f /opt/syco/var/rsyslog/rsyslogd.conf "+app.INSTALL_DIR+"rsyslog.conf" )

  # Initialize all passwords used by the script
  app.init_mysql_passwords()

  #Generating syslog user mysql passwors
  sqlpassword=generate_password(10,"jkshdkuiyuiwehdpooads8979878378yedhjcjsdgfdsjhgchjdsj")

  #applying sql password
  x("sed -i 's/SQLPASSWORD/"+sqlpassword+"/g' "+app.INSTALL_DIR+"initdb.sql")
  x("sed -i 's/SQLPASSWORD/"+sqlpassword+"/g' "+app.INSTALL_DIR+"rsyslog.conf")
  x("sed -i 's/SERVERNAME/"+net.get_hostname()+"."+config.general.get_resolv_domain()+"/g' "+app.INSTALL_DIR+"rsyslog.conf")
  x("sed -i 's/DOMAIN/"+config.general.get_resolv_domain()+"/g' "+app.INSTALL_DIR+"rsyslog.conf")

  # Setting upp Databas connections and rsyslog config
  x("mysql -h127.0.0.1 -u root -p'"+app.get_mysql_root_password()+"' -e 'CREATE DATABASE Syslog;'"  )
  x("mysql -u root -p'"+app.get_mysql_root_password()+"' Syslog< "+app.INSTALL_DIR+"initdb.sql")
  x("\cp -f "+app.INSTALL_DIR+"rsyslog.conf /etc/rsyslog.conf")

  #Fix up
  x("mkdir /var/log/remote")


  #Restarting service
  x("/etc/init.d/mysqld restart")
  x("/etc/init.d/rsyslog restart")




def rsyslog_newcerts(args):
  '''
  Script to generate new tls certs for rsyslog server and all klients.
  got to run one every year.
  Will get servers name from install.cfg and generat tls certs for eatch server listed.
  '''
  x("mkdir /etc/pki/rsyslog")
  hostname = net.get_hostname()+"."+config.general.get_resolv_domain()

  #Coping certs templatet
  x("\cp -f /opt/syco/var/rsyslog/template.ca "+app.INSTALL_DIR+"template.ca" )
  x("sed -i 's/SERVERNAME/"+net.get_hostname()+"."+config.general.get_resolv_domain()+"/g' "+app.INSTALL_DIR+"template.ca")
  x("sed -i 's/DOMAIN/"+config.general.get_resolv_domain()+"/g' "+app.INSTALL_DIR+"template.ca")


  #Making CA
  x("certtool --generate-privkey --outfile /etc/pki/rsyslog/ca-key.pem")
  x("certtool --generate-self-signed --load-privkey /etc/pki/rsyslog/ca-key.pem --outfile /etc/pki/rsyslog/ca.pem --template "+app.INSTALL_DIR+"template.ca")


  #Making rsyslog SERVER cert
  x("\cp -f /opt/syco/var/rsyslog/template.server "+app.INSTALL_DIR+"template."+hostname)
  x("sed -i 's/SERVERNAME/"+hostname+"/g' "+app.INSTALL_DIR+"template."+hostname)
  x("sed -i 's/SERIAL/1/g' "+app.INSTALL_DIR+"template."+hostname)
  x("sed -i 's/DOMAIN/"+config.general.get_resolv_domain()+"/g' "+app.INSTALL_DIR+"template."+hostname)




  x("certtool --generate-privkey --outfile /etc/pki/rsyslog/"+hostname+"-key.pem")
  x("certtool --generate-request --load-privkey /etc/pki/rsyslog/"+hostname+"-key.pem --outfile /etc/pki/rsyslog/"+hostname+"-req.pem --template "+app.INSTALL_DIR+"template."+hostname)
  x("certtool --generate-certificate --load-request /etc/pki/rsyslog/"+hostname+"-req.pem --outfile /etc/pki/rsyslog/"+hostname+"-cert.pem \
    --load-ca-certificate /etc/pki/rsyslog/ca.pem --load-ca-privkey /etc/pki/rsyslog/ca-key.pem --template "+app.INSTALL_DIR+"template."+hostname)

  #Making serialgenerate_password
  serial=2
  for server in get_servers():

    app.print_verbose("Generating tls certs for rsyslog client "+server)
    x("\cp -f /opt/syco/var/rsyslog/template.server "+app.INSTALL_DIR+"/template."+server)
    x("sed -i 's/SERVERNAME/"+server+"."+config.general.get_resolv_domain()+"/g' "+app.INSTALL_DIR+"template."+server)
    x("sed -i 's/SERIAL/"+str(serial)+"/g' "+app.INSTALL_DIR+"template."+server)
    x("sed -i 's/DOMAIN/"+config.general.get_resolv_domain()+"/g' "+app.INSTALL_DIR+"template."+server)

    x("certtool --generate-privkey --outfile /etc/pki/rsyslog/"+server+"."+config.general.get_resolv_domain()+"-key.pem")
    x("certtool --generate-request --load-privkey /etc/pki/rsyslog/"+server+"."+config.general.get_resolv_domain()+"-key.pem --outfile /etc/pki/rsyslog/"+server+"."+config.general.get_resolv_domain()+"-req.pem --template "+app.INSTALL_DIR+"template."+server)
    x("certtool --generate-certificate --load-request /etc/pki/rsyslog/"+server+"."+config.general.get_resolv_domain()+"-req.pem --outfile /etc/pki/rsyslog/"+server+"."+config.general.get_resolv_domain()+"-cert.pem \
        --load-ca-certificate /etc/pki/rsyslog/ca.pem --load-ca-privkey /etc/pki/rsyslog/ca-key.pem --template "+app.INSTALL_DIR+"template."+server)
    serial=serial+1




def uninstall_rsyslogd(args):
  '''
  Remove Rsyslogd server from the server

  '''
  return
  app.print_verbose("Uninstall Rsyslogd SERVER")
  x("yum erase rsyslog")
  x("rm -rf /etc/pki/rsyslog")
