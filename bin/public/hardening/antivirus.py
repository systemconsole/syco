#!/usr/bin/env python
'''
Installs antivirus - part of the hardening.

- Downloading clamav from clamav server
- Building clamav for host
- Setup database update in crontab
- Setup virus scan in crontab
- Setup cron job to scan and send email if infected files are found
- Report infected files to ADMIN_EMAIL

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

# Path to clam installation.
CLAM_AV_URL="http://downloads.sourceforge.net/project/clamav/clamav/0.97.4/clamav-0.97.4.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fclamav%2Ffiles%2FOldFiles%2F&ts=1335258374&use_mirror=switch"

import os
import urllib

import app
from general import x
import config
import scOpen


def install_antivirus():
	app.print_verbose("Install antivirus (clamav and freshclam).")

	#
	# Download and extract clamav
	#
	app.print_verbose("Download and extract clamav")
	urllib.urlretrieve (CLAM_AV_URL, "/tmp/clamav_latest.tar.gz")
	x("tar -C /tmp/ -zxvf /tmp/clamav_latest.tar.gz")
	x("rm -f /tmp/clamav_latest.tar.gz")

	#
	# Build and install clamav and freshclam
	#
	app.print_verbose("Build and install clamav and freshclam")
	x("/usr/sbin/adduser clamav --shell=/dev/null")
	x("mv /tmp/clamav-* /tmp/clamav-latest ")
	os.chdir("/tmp/clamav-latest")
	x("./configure")
	x("make")
	x("make install")
	x("rm -rf /tmp/clamav-latest/")

	#
	# Setup clamav and freshclam
	#
	app.print_verbose("Setup clamav and freshclam")
	x("mkdir /var/log/clamav")

	freshclam = scOpen("/usr/local/etc/freshclam.conf")
	freshclam.replace("^[\#]?Example.*",        "#Example")
	freshclam.replace("^[\#]?LogFileMaxSize.*", "LogFileMaxSize 100M")
	freshclam.replace("^[\#]?LogTime.*",        "LogTime yes")
	freshclam.replace("^[\#]?LogSyslog.*",      "LogSyslog yes")

	clamd = scOpen("/usr/local/etc/clamd.conf")
	clamd.replacE("^([\#]?)Example.*", 			  "#Example")
	clamd.replacE("^([\#]?)LogFileMaxSize.*", 	  "LogFileMaxSize 100M")
	clamd.replacE("^([\#]?)LogTime.*",            "LogTime yes")
	clamd.replacE("^([\#]?)LogSyslog.*",          "LogSyslog yes")
	clamd.replacE("^([\#]?)TCPSocket.*",          "TCPSocket 3310")
	clamd.replacE("^([\#]?)TCPAddr.*", 	          "TCPAddr 127.0.0.1")
	clamd.replacE("^([\#]?)ExcludePath.*/proc.*", "ExcludePath ^/proc")
	clamd.replacE("^([\#]?)ExcludePath.*/sys.*",  "ExcludePath ^/sys")

	#
	# Setup crontab
	#
	app.print_verbose("Setup crontab")
	x("cp %s/hardening/viruscan.sh /etc/cron.daily/" % app.SYCO_VAR_PATH)
	scOpen("/etc/cron.daily/viruscan.sh").replace(
		"${ADMIN_EMAIL}", config.general.get_admin_email()
	)

	#
	# Start clamd
	#
	app.print_verbose("Start clamd")
	x("/usr/local/sbin/clamd")

	#Finish
	app.print_verbose("ClavAV is now installed.")
