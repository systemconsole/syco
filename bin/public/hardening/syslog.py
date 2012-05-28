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


Harden Syslog
--------------------------------------------------
	- Set syslog to logg all actions on server to files.
	- If vsftp is installed set to log user actions
	- Conenct syslog to send all logs to syslog server 
'''


from shutil import copyfile
import fileinput
import sys
import ConfigParser
import config
import general
import app
from scopen import scOpen
from general import grep
import os

def syslog():
	app.print_verbose("Setting upp Rsyslog from CIS benchmark")

	#Verify that autpriv is enblaed in rsyslog.conf
	scOpen('/etc/rsyslog.conf').remove("^authpriv\\.\\*")
	scOpen('/etc/rsyslog.conf').add("authpriv.*\t\t\t\t/var/log/secure\n")

	# Verify that auth is enbladed in rsyslog.conf
	scOpen('/etc/rsyslog.conf').remove("^auth\\.\\*")
	scOpen('/etc/rsyslog.conf').add("auth.*\t\t\t\t/var/log/messages\n")

	# Secure VSFTP if installed.
	if os.path.isfile("/etc/vsftpd.conf"):
		general.set_config_property("/etc/vsftpd.conf","^([\#]?)xferlog_std_format=NO.*","xferlog_std_format=NO")
		general.set_config_property("/etc/vsftpd.conf","^([\#]?)log_ftp_protocol=YES.*","log_ftp_protocol=YES")
		app.print_verbose("Enabling user loggining vsftpd")
	
	if os.path.isfile("/etc/vsftpd/vsftpd.conf"):
		general.set_config_property("/etc/vsftpd.conf","^([\#]?)xferlog_std_format=NO","xferlog_std_format=NO")
		general.set_config_property("/etc/vsftpd.conf","^([\#]?)log_ftp_protocol=YES","log_ftp_protocol=YES")
		app.print_verbose("Enabling user loggining vsftpd")

	
def add_sysloghost():
	'''
	This function ad the syslog host to the rsyslog.conf.
	To set the syslog host please set in global config.
	'''

	general.set_config_property("/etc/rsyslog.conf","^([\#]?)\$ModLoad imudp.so","$ModLoad imudp.so")
	general.set_config_property("/etc/rsyslog.conf","^([\#]?)\$UDPServerRun.*","$UDPServerRun 514")
	general.set_config_property("/etc/rsyslog.conf","(?#)\*.\* @"+config.general.get_loggserver()+":514","*.* @"+config.general.get_loggserver()+":514")
	app.print_verbose("Setting logging to remote syslog")


def verify_syslog():
	if not grep("/etc/rsyslog.conf",'^auth\\.\\*'):
		#Do nothing only print if setting DONT excists in file
		print "ERROR Setting  auth are NOT in config file syslog_config"
	
	if not grep("/etc/rsyslog.conf",'^authpriv\\.\\*'):
		#Do nothing only print if setting DONT excists in file
		print "ERROR Setting  authpriv are NOT in config file syslog_config"
	
	if not grep("/etc/rsyslog.conf",'^\$ModLoad'):
		#Do nothing only print if setting DONT excists in file
		print "ERROR Setting modload imudp are NOT in config file syslog_config"
	
	if not grep("/etc/rsyslog.conf",'^\$UDPServerRun'):
		#Do nothing only print if setting DONT excists in file
		print "ERROR Setting UDP port are NOT in config file syslog_config"
	
	if not grep("/etc/rsyslog.conf",".*"+config.general.get_loggserver()):
		#Do nothing only print if setting DONT excists in file
		print "ERROR Setting syslogserver are NOT in config file syslog_config"

