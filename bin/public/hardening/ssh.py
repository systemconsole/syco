#!/usr/bin/env python
'''
Setup ssh - part of the hardening.

Reads config from var/hardening/config.cfg and set the settings to ssh/sshd.

- Settings ssh server restrictions for login and idle time
- Disable Root login
- Setting only to use protocol 2
- Setting new ssh banner

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import ConfigParser

from general import x
import app
from scopen import scOpen


def setup_ssh():
	app.print_verbose("Harden ssh and sshd.")
	x("cp /etc/ssh/ssh_config  /etc/ssh/ssh_config.sycobak")
	x("cp /etc/ssh/sshd_config /etc/ssh/sshd_config.sycobak")

	config = ConfigParser.SafeConfigParser()
	config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)

	#
	# Hardening ssh config
	#
	ssh = scOpen("/etc/ssh/ssh_config")
	for setting in config.options('ssh'):
		ssh.replace_add("^(?#)(?i)" + setting + ".*", config.get('ssh',setting))

	#
	# Hardening sshd config
	#
	ssh = scOpen("/etc/ssh/sshd_config")
	for setting in config.options('sshd'):
		ssh.replace_add(".*(?#)(?i)" + setting + ".*", config.get('sshd',setting))

	#
	# Set login banner.
	#
	x('cp %s/hardening/issue.net /etc/issue.net' % app.SYCO_VAR_PATH)
