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


Disable Service
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

import ConfigParser
import os
from general import disable_service
import app




def serviceOff():
	config = ConfigParser.SafeConfigParser()
	config.read(app.SYCO_VAR_PATH+'/hardening/config.cfg')
	for service in config.options('service'):
		if os.path.exists('/etc/xinetd.d/'+service):
			print "Disabling service"+service
			disable_service(service)	
		else:
			print "Service "+service+" Was not installed on this system"
				

		

	