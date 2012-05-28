#!/usr/bin/env python
'''

HARDENING 
-------------------------------------------------
Script for hardneing Centos / Redhate server according 
CIS standards.
http://www.cisecurity.org/

This is script is one of serverl scripts run to 
hardning server.
All scripts can be found in public/ hardening folder.

To harden en server run 
-----------------------
syco harden

To verify server status run
---------------------------
syco harden-verify

To harden SSH run
-----------------
syco harden-ssh


Antivirus setup
--------------------------------------------------
	- Downloading clamav from clamav server
	- Building clamav for host
	- Setting up datbase update in crontab
	- Setting up virus scan in crontab
        - Setting upp cron jobb to scan and send email if infected files are fount
        - Repport infected files to arenden@fareoffice.com

'''

__author__ = "mattias.hemmingsson@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "mattias.hemmingsson@fareoffice.com"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"



from shutil import copyfile
import fileinput
import sys
import ConfigParser
from general import download_file
from general import x
from general import grep
import general
import app
import constant
import urllib2, urllib
import os



def install_av():

	
	#Installing requerd yum programsprograms
	app.print_verbose("Installing yum pakeges needed for Clamav")
	x("yum install wget -y")



	'''
	Downloading and extracting clamav
	http://downloads.sourceforge.net/project/clamav/clamav/0.97.4/clamav-0.97.4.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fclamav%2Ffiles%2FOldFiles%2F&ts=1335258374&use_mirror=switch
	'''
	app.print_verbose("downloading and extracting clamav")
	urllib.urlretrieve ("http://downloads.sourceforge.net/project/clamav/clamav/0.97.4/clamav-0.97.4.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fclamav%2Ffiles%2FOldFiles%2F&ts=1335258374&use_mirror=switch", "/tmp/clamav_latest.tar.gz")
	x("tar -C /tmp/ -zxvf  /tmp/clamav_latest.tar.gz")
	x("rm -f /tmp/clamav_latest.tar.gz")


	
	#Buldning and installing clamav
	app.print_verbose("Building and setting upp Clamav and Freshclam")
  #	constant.INSTALL_DIR?
	x("/usr/sbin/adduser clamav --shell=/dev/null")
	x("mv /tmp/clamav-* /tmp/clamav-latest ")
	os.chdir("/tmp/clamav-latest")
	x("./configure") 	
	x("make")
	x("make install")
	


	
	#Setting up clamav and freshclam
	general.set_config_property("/usr/local/etc/freshclam.conf","^[\#]?Example.*","#Example")
	general.set_config_property("/usr/local/etc/freshclam.conf","^[\#]?LogFileMaxSize.*","LogFileMaxSize 100M")
	general.set_config_property("/usr/local/etc/freshclam.conf","^[\#]?LogTime.*","LogTime yes")
	general.set_config_property("/usr/local/etc/freshclam.conf","^[\#]?LogSyslog.*","LogSyslog yes")

	general.set_config_property("/usr/local/etc/clamd.conf","^([\#]?)Example.*","#Example")
	general.set_config_property("/usr/local/etc/clamd.conf","^([\#]?)LogFileMaxSize.*","LogFileMaxSize 100M")
	general.set_config_property("/usr/local/etc/clamd.conf","^([\#]?)LogTime.*","LogTime yes")
	general.set_config_property("/usr/local/etc/clamd.conf","^([\#]?)LogSyslog.*","LogSyslog yes")
	general.set_config_property("/usr/local/etc/clamd.conf","^([\#]?)TCPSocket.*","TCPSocket 3310")
	general.set_config_property("/usr/local/etc/clamd.conf","^([\#]?)TCPAddr.*","TCPAddr 127.0.0.1")
	general.set_config_property("/usr/local/etc/clamd.conf","^([\#]?)ExcludePath.*/proc.*","ExcludePath ^/proc")
	general.set_config_property("/usr/local/etc/clamd.conf","^([\#]?)ExcludePath.*/sys.*","ExcludePath ^/sys")

	x("/usr/local/sbin/clamd")
	x("mkdir /var/log/clamav")
	x("cp "+app.SYCO_VAR_PATH+"/hardening/viruscan.sh /etc/cron.daily/")
        
    #Cleaning upp by remving yum packages
	app.print_verbose("Cleaning up clamav installation")
	x("yum remove wget -y")
	x("rm -rf /tmp/clamav-latest/")

	#Finnish
	app.print_verbose("ClavAV is now installed and settup on you server") 