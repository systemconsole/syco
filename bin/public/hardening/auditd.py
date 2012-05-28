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


Auditd setup
--------------------------------------------------
Audid the lets you monitor changes made to files on you host.

	- Setting upp auditd 
	- Setting permission on auditf files
	- Copying in new rules file to use
	- Restaring auditd
        
'''
from shutil import copyfile
import fileinput
import sys
import ConfigParser
import general
from general import x
import app
from general import grep

def auditd():
	'''
	Setting upp auditd rules
	coping rules fil from var to audit.d folder
	'''
	app.print_verbose("Setting up auditd for file monitoring")
	x("rm /etc/audit/audit.rules")
	x("cp "+app.SYCO_VAR_PATH+"/audit.rules /etc/audit/audit.rules")
	x("chmod 700 /etc/audit/audit.rules")

	'''
	Harding auddit.conf file
	'''
	general.set_config_property("/etc/audit/auditd.conf","^num_logs.*","num_logs = 5")
	general.set_config_property("/etc/audit/auditd.conf","^max_log_file.*","max_log_file = 100")
	general.set_config_property("/etc/audit/auditd.conf","^space_left.*","space_left = 125")
	general.set_config_property("/etc/audit/auditd.conf","^admin_space_left.*","admin_space_left = 75")
	x("chmod 700 /etc/audit/auditd.conf")
	
	#Enabling auditd and syslog after reboots
	x("chkconfig --list auditd")
	x("chkconfig --level 35 auditd on")
	

	#Restarting service
	x("service auditd restart")
	app.print_verbose("auditd is now insatalled and setup on your server")