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


Password setup
--------------------------------------------------
	Setting users right and locking down password settings.
	Forcing the user to password restrictions.

	- Setting login shell to /dev/null for system accounts
	- Disabling accounts with empty passwords
	- Locing accounds in shadow with !! instead of ! ore *
	- Setting password expire settings 
	- Setting password complexity
	




'''
__author__ = "mattias.hemmingsson@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "mattias.hemmingsson@fareoffice.com"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import ConfigParser
import stat
from shutil import copyfile
import fileinput
import sys

import app
import general
from general import x


def hardenPassword():
	app.print_verbose("Setting login shell to '/dev/null' for system accounts")
	users = open("/etc/passwd")
	userlist=[]
	for line in users:
		userid = int(line.split(':')[2]);
		username = line.split(':')[0];

		if userid == 0 or userid > 499:
			pass
		else:
			x("usermod -L -s /dev/null "+username)
	
	# Verify so that now empty passwords are in shadow file
	shadow = open("/etc/shadow")
	for line in shadow:
		shadowpass = line.split(':')[1]
		shadowuser = line.split(':')[0]
		if shadowpass == "" or shadowpass == " ":
			x("usermod -L -s /dev/null " + shadowuser)
			app.print_verbose("Diable user " + shadowuser + " hade emty password")
	app.print_verbose("Verified so that no emty passwords is found. And if so locking that account")                
    
	# Repacling all lock accounts in /etc/shadow by replacing
	# * and ! to !!
	replaceShadow("/etc/shadow",":!:",":!!:")
	replaceShadow("/etc/shadow",":*:",":!!:")
	app.print_verbose("Locking accountd in shadow with !! instead of * and !")

	# Set Account Expiration Parameters On Active Accounts
	app.print_verbose("Set Account Expiration Parameters On Active Accounts")
	general.set_config_property("/etc/login.defs","^PASS_MAX_DAYS.*","PASS_MAX_DAYS\t90")
	general.set_config_property("/etc/login.defs","^PASS_MIN_DAYS.*","PASS_MIN_DAYS\t7")
	general.set_config_property("/etc/login.defs","^PASS_WARN_AGE.*","PASS_WARN_AGE\t14")
	general.set_config_property("/etc/login.defs","^PASS_MIN_LEN.*","PASS_MIN_LEN\t9")
	app.print_verbose("Account Expiration Parameters On Active Accounts set")
	
	# Setting pam to enforce complex passwords 
	# 3 tries to change password (retry=3)
	# 9 entries mini lenght (minlen=9)
	# 3 entries must differ from last password (difok=3)
	# 1 lover case letter miminmum (lcredit=1)
	# 1 upper case letter minimum (ucredit=1)
	# 1 digits minimu (dcredit=1)
	# 2 other caracter (ocredit=2)
	general.set_config_property("/etc/pam.d/system-auth","^password.*requisite.*pam_cracklib.so.*","password\trequisite\tpam_cracklib.so try_first_pass retry=3 minlen=9 difok=3 lcredit=1 ucredit=1 dcredit=1 ocredit=2")
	app.print_verbose("Password restrections set")
       
	# Setting upp account lock efter 5 error login
	# Admin must unlock account
	general.set_config_property("/etc/pam.d/system-auth","^auth.*required.*pam_tally.so.*","auth\trequired\tpam_tally.so onerr=fail deny=5")
	app.print_verbose("Account locked after 5 error login set")


def replaceShadow(file,searchExp,replaceExp):
    for line in fileinput.input(file,inplace=1):
        if searchExp in line:
        	line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)
