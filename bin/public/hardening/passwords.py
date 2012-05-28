#!/usr/bin/env python
'''
Harden password policy - part of the hardening.

- Set login shell to /dev/null for system accounts
- Disabling accounts with empty passwords
- Locking accounts in shadow with !! instead of ! or *
- Set password expire
- Set password complexity

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import fileinput
import sys

import app
from general import x
import scOpen


def harden_password():
	app.print_verbose("Harden password")

	#
	# Set login shell to /dev/null
	#
	app.print_verbose("Set login shell to '/dev/null' for system accounts")
	users = open("/etc/passwd")
	for line in users:
		userid = int(line.split(':')[2]);
		username = line.split(':')[0];

		if userid > 0 and userid <= 499:
			x("usermod -L -s /dev/null %s" % username)

	#
	# Disable users with empty passwords in the shadow file.
	#
	app.print_verbose("Disable users with empty passwords in the shadow file.")
	shadow = open("/etc/shadow")
	for line in shadow:
		shadowpass = line.split(':')[1]
		shadowuser = line.split(':')[0]
		if shadowpass.strip() == "":
			x("usermod -L -s /dev/null " + shadowuser)
			app.print_verbose("Diable user %s with empty password." %  shadowuser)

	#
	# Modify locked accounts in /etc/shadow by replacing * and ! to !!
	#
	app.print_verbose(
		"Modify locked accounts in /etc/shadow by replacing * and ! to !!"
	)
	replaceShadow("/etc/shadow", ":!:",":!!:")
	replaceShadow("/etc/shadow", ":*:",":!!:")

	#
	# Set account expiration parameters on active accounts
	#
	app.print_verbose("Set account expiration parameters on active accounts")
	login_defs = scOpen("/etc/login.defs")
	login_defs.replace("^PASS_MAX_DAYS.*", "PASS_MAX_DAYS\t90")
	login_defs.replace("^PASS_MIN_DAYS.*", "PASS_MIN_DAYS\t7")
	login_defs.replace("^PASS_WARN_AGE.*", "PASS_WARN_AGE\t14")
	login_defs.replace("^PASS_MIN_LEN.*",  "PASS_MIN_LEN\t9")

	#
	# Set pam to enforce complex passwords
	# 3 tries to change password (retry=3)
	# 9 entries mini lenght (minlen=9)
	# 3 entries must differ from last password (difok=3)
	# 1 lover case letter miminmum (lcredit=1)
	# 1 upper case letter minimum (ucredit=1)
	# 1 digits minimu (dcredit=1)
	# 2 other caracter (ocredit=2)
	#
	app.print_verbose("Set pam to enforce complex passwords")
	scOpen("/etc/pam.d/system-auth").replace(
		"^password.*requisite.*pam_cracklib.so.*",
		"password\trequisite\tpam_cracklib.so try_first_pass retry=3 " +
		"minlen=9 difok=3 lcredit=1 ucredit=1 dcredit=1 ocredit=2"
	)

	#
	# Lock accounts after 5 failed login attempts. Admin must unlock account.
	#
	app.print_verbose("Lock accounts after 5 failed login attempts.")
	scOpen("/etc/pam.d/system-auth").replace(
		"^auth.*required.*pam_tally.so.*",
		"auth\trequired\tpam_tally.so onerr=fail deny=5"
	)

	#
	# Store passwords in sha512 instead of md5
	#
  	app.print_verbose("   Store passwords sha512 instead of md5")
  	x("authconfig --passalgo=sha512 --update --disablefingerprint")



def replaceShadow(file,searchExp,replaceExp):
    for line in fileinput.input(file,inplace=1):
        if searchExp in line:
        	line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)
