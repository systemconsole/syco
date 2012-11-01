#!/usr/bin/env python
'''
Setup syslog - part of the hardening.

- Set syslog to log all actions on server to files.
- If vsftp is installed set to log user actions.
- Connect syslog to send all logs to syslog server.


@TODO: Move to install-rsyslogd.
'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import config
import app
from scopen import scOpen
from general import x
import os


def setup_syslog():
	syslog()
	setup_remote_loging()


def syslog():
	app.print_verbose("CIS 5.2 Configure rsyslog")

	#
	app.print_verbose("CIS 5.2.1 Install the rsyslog package")
	x("yum install rsyslog")

	#
	app.print_verbose("CIS 5.2.2 Activate the rsyslog Service")
	if os.path.exists('/etc/xinetd.d/syslog'):
		x("chkconfig syslog off")
	x("chkconfig rsyslog on")

	#
	app.print_verbose("CIS 5.2.3 Configure /etc/rsyslog.conf")
	# >> etc/rsyslog.conf
	# auth,user.* 	/var/log/messages
	# kern.*			/var/log/kern.log
	# daemon.*		/var/log/daemon.log
	# syslog.* 		/var/log/syslog
	# lpr,news,uucp,local0,local1,local2,local3,local4,local5,local6.* /var/log/unused.log

	# x("pkill -HUP rsyslogd")

	#
	app.print_verbose("CIS 5.2.4 Create and Set Permissions on rsyslog Log Files")
	# for logfile in all_files_in_rsyslog.conf
	# touch logfile
	# chown root:root logfile
	# chmod og-rwx logfile

	#
	# Enable autpriv in rsyslog.conf
	#
	rsyslog = scOpen('/etc/rsyslog.conf')
	rsyslog.remove("^authpriv\\.\\*")
	rsyslog.add("authpriv.*\t\t\t\t/var/log/secure\n")


	#
	# Enable auth in rsyslog.conf
	#
	rsyslog.remove("^auth\\.\\*")
	rsyslog.add("auth.*\t\t\t\t/var/log/messages\n")

	#
	# Secure VSFTP if installed.
	#
	if os.path.isfile("/etc/vsftpd.conf"):
		app.print_verbose("Enable user logining for vsftpd.")
		ftp = scOpen("/etc/vsftpd.conf")
		ftp.replace("^([\#]?)xferlog_std_format=NO.*", "xferlog_std_format=NO")
		ftp.replace("^([\#]?)log_ftp_protocol=YES.*",  "log_ftp_protocol=YES")

	if os.path.isfile("/etc/vsftpd/vsftpd.conf"):
		app.print_verbose("Enable user logining for vsftpd.")
		ftp = scOpen("/etc/vsftpd.conf")
		ftp.replace("^([\#]?)xferlog_std_format=NO", "xferlog_std_format=NO")
		ftp.replace("^([\#]?)log_ftp_protocol=YES",  "log_ftp_protocol=YES")


def setup_remote_loging():
	'''
	Setup remote loging.

	All logs to this server are forwarded to remote log server.

	'''
	app.print_verbose("CIS 5.2.5 Configure rsyslog to Send Logs to a Remote Log Host.")
	log = scOpen("/etc/rsyslog.conf")
	log.replace_add("^([\#]?)\$ModLoad imudp.so", "$ModLoad imudp.so")
	log.replace_add("^([\#]?)\$UDPServerRun.*",   "$UDPServerRun 514")
	log.replace(
		"(?#)\*.\* @"+config.general.get_log_server_hostname()+":514",
		"*.* @"+config.general.get_log_server_hostname()+":514"
	)
