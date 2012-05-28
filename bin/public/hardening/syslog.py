#!/usr/bin/env python
'''
Setup syslog - part of the hardening.

- Set syslog to log all actions on server to files.
- If vsftp is installed set to log user actions.
- Connect syslog to send all logs to syslog server.

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
from general import grep
import os


def setup_syslog():
	syslog()
	setup_remote_logging()


def syslog():
	app.print_verbose("Setup rsyslog from CIS benchmark")

	#
	# Enable autpriv in rsyslog.conf
	#
	scOpen('/etc/rsyslog.conf').remove("^authpriv\\.\\*")
	scOpen('/etc/rsyslog.conf').add("authpriv.*\t\t\t\t/var/log/secure\n")

	#
	# Enable auth in rsyslog.conf
	#
	scOpen('/etc/rsyslog.conf').remove("^auth\\.\\*")
	scOpen('/etc/rsyslog.conf').add("auth.*\t\t\t\t/var/log/messages\n")

	#
	# Secure VSFTP if installed.
	#
	if os.path.isfile("/etc/vsftpd.conf"):
		app.print_verbose("Enable user loggining for vsftpd.")
		ftp = scOpen("/etc/vsftpd.conf")
		ftp.replace("^([\#]?)xferlog_std_format=NO.*", "xferlog_std_format=NO")
		ftp.replace("^([\#]?)log_ftp_protocol=YES.*",  "log_ftp_protocol=YES")

	if os.path.isfile("/etc/vsftpd/vsftpd.conf"):
		app.print_verbose("Enable user loggining for vsftpd.")
		ftp = scOpen("/etc/vsftpd.conf")
		ftp.replace("^([\#]?)xferlog_std_format=NO", "xferlog_std_format=NO")
		ftp.replace("^([\#]?)log_ftp_protocol=YES",  "log_ftp_protocol=YES")


def setup_remote_logging():
	'''
	Setup remote logging.

	All logs to this server are forwarded to remote log server.

	'''
	app.print_verbose("Setup remote logging.")
	log = scOpen("/etc/rsyslog.conf")
	log.replace("^([\#]?)\$ModLoad imudp.so", "$ModLoad imudp.so")
	log.replace("^([\#]?)\$UDPServerRun.*",   "$UDPServerRun 514")
	log.replace(
		"(?#)\*.\* @"+config.general.get_loggserver()+":514",
		"*.* @"+config.general.get_loggserver()+":514"
	)


def verify_syslog():
	if not grep("/etc/rsyslog.conf", '^auth\\.\\*'):
		app.print_error("auth are NOT in config file syslog_config")

	if not grep("/etc/rsyslog.conf", '^authpriv\\.\\*'):
		app.print_error("authpriv are NOT in config file syslog_config")

	if not grep("/etc/rsyslog.conf", '^\$ModLoad'):
		app.print_error("modload imudp are NOT in config file syslog_config")

	if not grep("/etc/rsyslog.conf", '^\$UDPServerRun'):
		app.print_error("UDP port are NOT in config file syslog_config")

	if not grep("/etc/rsyslog.conf", ".*"+config.general.get_loggserver()):
		app.print_error("syslogserver are NOT in config file syslog_config")

