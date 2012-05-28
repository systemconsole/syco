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


Harden SSH
--------------------------------------------------
	Reads congifile located in var/hardningen/config.cfg
	And set the settings to ssh configfile.
	To add ore delet settings edit config.cfg file.

	- Settings ssh server restrictions for login and idle time
	- Disable Root login 
	- Setting only to use protocol 2
	- Setting new ssh banner

	

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
from general import grep
import general
from app import print_verbose


def hardenSSH():
	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')
	#baking backup copy of files
	copyFile("/etc/ssh/ssh_config")
	copyFile("/etc/ssh/sshd_config")

	#Hardning ssh config
	for setting in config.options('ssh'):
		general.set_config_property("/etc/ssh/ssh_config","^(?#)(?i)" + setting + ".*",config.get('ssh',setting))

	#Hardning sshd config
	for setting in config.options('sshd'):
		general.set_config_property("/etc/ssh/sshd_config",".*(?#)(?i)" + setting + ".*",config.get('sshd',setting))	

	copyfile(app.SYCO_VAR_PATH+'/hardening/issue.net','/etc/issue.net')


def verifySSH():
	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')
	for setting in config.options('ssh'):
		if not grep("/etc/ssh/sshd_config",config.get('ssh',setting)):
			#Do nothing only print if setting DONT excists in file
			print_verbose("ERROR Setting " + setting + " are NOT in config file ssh_config")

	for setting in config.options('sshd'):
		if not grep("/etc/ssh/sshd_config",config.get('sshd',setting)):
			#Do nothing only print if setting DONT excists in file
			print_verbose("ERROR Setting " + setting + " are NOT in config file sshd_config")


def copyFile(filename):
	copyfile(filename, filename+"_syco_backup")


