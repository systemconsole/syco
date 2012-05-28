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


Network setup
--------------------------------------------------
	Setting network settings for host to deny differnt settings.
	Exempel settnings to deny are redir traffic trow host.
	Size of package.
	All Settings are locate in var/hardening/config.cfg file.



WARNING 
---------------------------------------------------
This script should not be run on server acting like routers aore gatewats.
All traffick going trow the host will be blocked.



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
import general
import app
from general import grep


def network():
	'''
    Disabling network settings on server
    '''
        
	app.print_verbose("Disable Network settings from CIS benchmark")

	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')

	#Harden network config
	for setting in config.options('network'):
		general.set_config_property("/etc/sysctl.conf","^" + setting + ".*$",config.get('network',setting))
		app.print_verbose("Server network settings " + setting + " has bean locked down")        

	
def verify_network():
	'''
    Verify that the network configsettings in the hardning config file has 
    bean applied.
    '''
        
	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')
	for setting in config.options('network'):
		if grep("/etc/sysctl.conf",config.get('network',setting)):
			#Do nothing only print if setting DONT excists in file
			pass
		else:
			print "ERROR Setting " + setting + " are NOT in config file sysctl_config"

	app.print_verbose("Network settings has bean verify")