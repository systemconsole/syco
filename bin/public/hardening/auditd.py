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
	auditd.replace_add("^max_log_file[\s]*\=.*",       "max_log_file = 50")

	app.print_verbose("CIS 5.3.2.2 Disable System on Audit Log Full")
	auditd.replace_add("^space_left_action[\s]*\=.*",       "space_left_action = email")
	auditd.replace_add("^action_mail_acct[\s]*\=.*",        "action_mail_acct = root")
	auditd.replace_add("^admin_space_left_action[\s]*\=.*", "admin_space_left_action = halt")

	app.print_verbose("CIS 5.3.2.3 Keep All Auditing Information")
	auditd.replace_add("^max_log_file_action[\s]*\=.*", "max_log_file_action = keep_logs")

	app.print_verbose("Extra auditd configs")
	auditd.replace_add("^num_logs[\s]*\=.*",                "num_logs = 99")
	auditd.replace_add("^space_left[\s]*\=.*",              "space_left = 125")
	auditd.replace_add("^admin_space_left[\s]*\=.*",        "admin_space_left = 75")

	x("chmod 700 /etc/audit/auditd.conf")

	#
	app.print_verbose("CIS 5.3.3 Enable Auditing for Processes That Start Prior to auditd")
	auditd = scOpen("/etc/grub.conf")
	auditd.add_to_end_of_line("^[^#]*kernel", "audit=1")

	# Addin audit to pam
	app.print_verbose("Logging all admin Actions")
	pam = scOpen("/etc/pam.d/systemauth")
	pam.replace_add("^session[\s]required[\s]pam_tty_audit.so[\s]enable=","session\trequired\tpam_tty_audit.so enable=*")

	# Making audit to log to syslog
	app.print_verbose("Sending all admin actions to Syslog")
	syslog = scOpen("/etc/audisp/plugins.d/syslog.conf")
	syslog.replace_add("^active[\s]=.*","active = yes")



	#Adding audit log compress service
	x('mkdir /opt/scripts/')
	x('cp /opt/syco/var/audit/audit_log_compress_daly.sh /opt/scripts/audit_log_compress_daly.sh')
	x('chmod 700 /opt/scripts/audit_log_compress_daly.sh')
	crontab = scOpen("/etc/crontab")
	crontab.remove("^00.*/audit_log_compress_daly.sh")
	crontab.add("'00   2 \* \* \*    root 	/opt/scripts/audit_log_compress_daly.sh'")

	x('Audit Log Compress installed')

	#
	# Restarting service
	#

	x("service auditd restart")
