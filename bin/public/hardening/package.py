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


Package setup
--------------------------------------------------
	Removning packages listed in config file from the host.
	All packaged NOT needet ore wanted on host should be listet in config file
	All Settings are locate in var/hardening/config.cfg file.




'''
__author__ = "mattias.hemmingsson@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "mattias.hemmingsson@fareoffice.com"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import ConfigParser
import app
from general import rpm_remove


def removePackage():
        '''
        Script for removing yum packages on server
        '''
	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')
	remove=""
	for package in config.options('package'):
		rpm_remove(package)
        app.print_verbose("Removing the following yum packaes from server " + remove)
		
