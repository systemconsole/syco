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
from scopen import scOpen


def install_auditd():
	app.print_verbose("Install auditd.")
	#
	# Setup auditd rules
	#
	app.print_verbose("CIS 5.3 Configure System Accounting (auditd)")

	app.print_verbose("CIS 5.3.1 Enable auditd Service")
	x("chkconfig auditd on")

	app.print_verbose("Added our own audit.rules")
	x("[ -f '/etc/audit/audit.rules' ] && rm /etc/audit/audit.rules")
	x("cp %shardening/audit.rules /etc/audit/audit.rules" % app.SYCO_VAR_PATH)
	x("chmod 700 /var/log/audit/")
	x("chmod 700 /etc/audit/audit.rules")

	#
	# Harding audit.conf file
	#
	auditd = scOpen("/etc/audit/auditd.conf")

	app.print_verbose("CIS 5.3.2.1 Configure Audit Log Storage Size")
	auditd.replace("^max_log_file[\s]*\=.*",       "max_log_file = 50")

	app.print_verbose("CIS 5.3.2.2 Disable System on Audit Log Full")
	auditd.replace("^space_left_action[\s]*\=.*",       "space_left_action = email")
	auditd.replace("^action_mail_acct[\s]*\=.*",        "action_mail_acct = root")
	auditd.replace("^admin_space_left_action[\s]*\=.*", "admin_space_left_action = halt")

	app.print_verbose("CIS 5.3.2.3 Keep All Auditing Information")
	auditd.replace("^max_log_file_action[\s]*\=.*", "max_log_file_action = keep_logs")

	app.print_verbose("Extra auditd configs")
	auditd.replace("^num_logs[\s]*\=.*",                "num_logs = 1024")
	auditd.replace("^space_left[\s]*\=.*",              "space_left = 125")
	auditd.replace("^admin_space_left[\s]*\=.*",        "admin_space_left = 75")

	x("chmod 700 /etc/audit/auditd.conf")

	#
	app.print_verbose("CIS 5.3.3 Enable Auditing for Processes That Start Prior to auditd")
	auditd = scOpen("/etc/grub.conf")
	auditd.add_to_end_of_line("^[^#]*kernel", " audit=1")

	#
	# Restarting service
	#
	x("service auditd restart")
