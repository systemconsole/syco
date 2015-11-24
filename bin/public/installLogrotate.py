#!/usr/bin/env python
"""
Install/configure logrotate.

"""

__author__ = "daniel@cybercow.se"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from general import x
from scopen import scOpen
import os
import app
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    """
    Defines the commands that can be executed through the syco.py shell script.

    """
    commands.add("install-logrotate", install_logrotate, help="Install/configure logrotate.")


def install_logrotate(args):
    """
    Install/configure logrotate.

    """
    app.print_verbose("Install/configure logrotate.")
    version_obj = version.Version("InstallLogrotate", SCRIPT_VERSION)
    version_obj.check_executed()

    sc = scOpen("/etc/logrotate.conf")
    sc.replace('#compress', 'compress')

    syslog_rotate()
    httpd_rotate()
    mysqld_rotate()

    version_obj.mark_executed()


def syslog_rotate():
    app.print_verbose("Adding syslog")
    x("mkdir -p /var/log/archive")
    x("cp %svar/logrotate/syslog /etc/logrotate.d/" % app.SYCO_PATH)


def httpd_rotate():
    if not os.path.exists('/etc/init.d/httpd'):
        return

    app.print_verbose("Adding httpd logrotate")
    x("mkdir -p /var/log/httpd/archive")
    x("cp %svar/logrotate/httpd /etc/logrotate.d/" % app.SYCO_PATH)


def mysqld_rotate():
    if not os.path.exists('/etc/init.d/mysqld'):
        return

    app.print_verbose("Adding mysqld-slow logrotate")
    x("cp %svar/logrotate/mysqld /etc/logrotate.d/" % app.SYCO_PATH)
