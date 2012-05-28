#!/usr/bin/env python
'''
Installs auditd - part of the hardening.

Auditd monitor changes made to files on the server.

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"



from general import x
import app
import scOpen


def install_auditd():
	app.print_verbose("Install auditd.")
	#
	# Setup auditd rules
	#
	app.print_verbose("Setup auditd for file monitoring.")
	x("rm /etc/audit/audit.rules")
	x("cp %s/audit.rules /etc/audit/audit.rules" % app.SYCO_VAR_PATH)
	x("chmod 700 /etc/audit/audit.rules")

	#
	# Harding auddit.conf file
	#
	auditd = scOpen("/etc/audit/auditd.conf")
	auditd.replace("^num_logs.*",         "num_logs = 5")
	auditd.replace("^max_log_file.*",     "max_log_file = 100")
	auditd.replace("^space_left.*",       "space_left = 125")
	auditd.replace("^admin_space_left.*", "admin_space_left = 75")
	x("chmod 700 /etc/audit/auditd.conf")

	#
	# Autostart auditd after reboots
	#
	x("chkconfig --list auditd")
	x("chkconfig --level 35 auditd on")

	#
	# Restarting service
	#
	x("service auditd restart")
	app.print_verbose("Auditd is now installed.")
