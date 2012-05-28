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


Host Permission setup
--------------------------------------------------
	- Chmod folder according to configfile
    - Chmod files according to confgifiles
    - Verfiy chmod files settings
    - Finding rouge files on system
    - Setting only root login from console
    - Lock down singel boot fucntion
    - Setting dmask on system
    - Disabling core dumps on system
    - Disabling su for users in wheel group (cant run sudo su)
	

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
import app
import ConfigParser
import stat
import general
from general import x
import sys
from shutil import copyfile
import fileinput
from scopen import scOpen

def chmod_folders():
	'''
	Setting chmod on folder from configfile
	'''
	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')

	#Hardning folders
	for setting in config.options('chmod_d'):
		cdir = config.get('chmod_d',setting)
		if os.path.isdir(cdir):
			x("chmod "+setting+" "+cdir)
	app.print_verbose("Folders chmod permission has bean set")		



def chmod_files():
	'''
	Setting chmod on files from configfile
	'''
	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')

	#Hardning files
	for setting in config.options('chmod_f'):
		fil = config.get('chmod_f',setting)
		if os.path.isfile(fil):
			os.chmod(fil,int(setting))
			app.print_verbose("Setting chmod "+fil+" on file "+setting)
        app.print_verbose("Files chmod permissions has bean set")               


def verify_chmod_files():
	'''
	Verfifying chmod files from config file.
	'''
	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')
	for setting in config.options('chmod_f'):
		fil = config.get('chmod_f',setting)
		if os.path.isfile(fil):
			app.print_verbose("%s : %s" % (fil, stat.S_IMODE(os.lstat(fil).st_mode)))
	app.print_verbose("chmod files verifing is done")       


def verify_no_rouge_files():
	'''
	Script that will find and print all file and folders thar are own by users not in the system
	and are located in the /etc folder
	'''

	users = open("/etc/passwd")
	userlist=[]
	for line in users:
		userid = line.split(':');
		userlist.append(userid[2])
	print userlist

	for dirname, dirnames, filenames in os.walk('/etc'):
		for subdirname in dirnames:
			stat_info = os.stat(os.path.join(dirname, subdirname))
			uid = stat_info.st_uid
			gid = stat_info.st_gid
			if str(uid) not in userlist:
				print "this folder "+os.path.join(dirname, subdirname)+" has strange user "+str(uid) 

		for filename in filenames:
			stat_info = os.stat(os.path.join(dirname, filename))
			uid = stat_info.st_uid
			gid = stat_info.st_gid
			if str(uid) not in userlist:
				print "this file "+os.path.join(dirname, filename)+" has strange user "+str(uid)

        app.print_verbose("Search for rouge files/ folders done")


def onlyRoot_console():
	'''
	Setting so that only root is alloed to login 
	with console
	'''
	copyfile("/etc/securetty","/etc/securetty_syco_backup")
	changefile = open("/etc/securetty",'w')
	changefile.write("tty1")
	app.print_verbose("Lockings down /etc/securetty for ROOT login only on tty1")


def lockdown_pysical():
	'''
	This locks down the singeluser mode. Witch lets an user start the server in "recoverymode" and 
	the set an user password

	'''
	app.print_verbose("Enable Authentication for Single-User Mode")
	general.set_config_property("/etc/inittab","^([\#]?)id:3:initdefault:","#id:3:initdefault:")
	general.set_config_property("/etc/inittab","^~~:S:wait:/sbin/sulogin.*","~~:S:wait:/sbin/sulogin")

	app.print_verbose("Disable Interactive Hotkey Startup at Boot")
	general.set_config_property("/etc/sysconfig/init","^PROMPT.*","PROMPT=no")	


def setting_dmask():
	'''
	Setting the defult dmask for all users and root. User can override this in private files in home folder

	'''
	#Setting umaskin system files
	scOpen('/etc/profile').replace('002','077')
	scOpen('/etc/profile').replace('027','077')

	scOpen('/etc/bashrc').replace('002','077')
	scOpen('/etc/bashrc').replace('027','077')

	scOpen('/etc/csh.cshrc').replace('002','077')
	scOpen('/etc/csh.cshrc').replace('027','077')

	scOpen('/etc/csh.login').replace('002','077')
	scOpen('/etc/csh.login').replace('027','077')
	
	
	#Setting emask in user files
	general.set_config_property("/etc/skel/.bachrc","^umask.*0777.*","umask 0777")
	general.set_config_property("/root/.bachrc","^umask.*0777.*","umask 0777")
	general.set_config_property("/root/.cshrc","^umask.*0777.*","umask 0777")
	general.set_config_property("/root/.tcshrc","^umask.*0777.*","umask 0777")
	app.print_verbose("DMASK settings on server has bean set")


def disble_coredumps():
	'''
	Disbling su that cure dump.
	Core dump is an file with the system memory in for error handling for developers.
	'''
	general.set_config_property("/etc/security/limits.conf","\\*.*hard.*core.*0","* hard core 0")
	general.set_config_property("/etc/sysctl.conf","^fs.suid_dumpable.*=.*0","fs.suid_dumpable = 0")
	x("sysctl -p")
	general.set_config_property("/etc/profile","^ulimit.*-S.*-c.*0.*>.*/dev/null.*2>&1","ulimit -S -c 0 > /dev/null 2>&1")
	app.print_verbose("Coredumps has bean disabled")


def disable_wheelsu():
	'''
	Disbling su fo user not in the wheel group
	'''
	general.set_config_property("/etc/pam.d/su","^([\#]?)auth.*required.*pam_wheel.so.*use_uid","auth\t\trequired\t\tpam_wheel.so use_uid")
	app.print_verbose("Su has bean disable for user not in wheel group")


