#!/usr/bin/env python
'''
Install/configure logrotate.

'''

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
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-logrotate", install_logrotate, help="Install/configure logrotate.")


def install_logrotate(args):
    '''
    Install/configure logrotate.

    '''
    app.print_verbose("Install/configure logrotate.")
    version_obj = version.Version("InstallLogrotate", SCRIPT_VERSION)
    version_obj.check_executed()

    sc = scOpen("/etc/logrotate.conf")
    sc.replace('#compress', 'compress')

    x("mkdir /var/log/archive")
    x("cp %s var/logrotate/syslog /etc/logrotate.d/" % app.SYCO_PATH)

    httpd_rotate()
    mysqld_rotate()
    auditd_rotate()
    install_SELinux()

    version_obj.mark_executed()

def httpd_rotate():
    if (not os.path.exists('/etc/init.d/httpd')):
       return

    app.print_verbose("Adding httpd logrotate")
    x("mkdir /var/log/httpd/archive")
    x("cp %svar/logrotate/httpd /etc/logrotate.d/" % app.SYCO_PATH)

def mysqld_rotate():
    if (not os.path.exists('/etc/init.d/mysqld')):
       return

    app.print_verbose("Adding mysqld-slow logrotate")
    x("cp %s var/logrotate/mysqld /etc/logrotate.d/" % app.SYCO_PATH)

def auditd_rotate():
    if (not os.path.exists('/etc/init.d/auditd')):
       return

    app.print_verbose("Adding audit logrotate")
    x("mkdir /var/log/audit/archive")
    x("cp %svar/logrotate/audit /etc/logrotate.d/" % app.SYCO_PATH)
    x("restorecon -r /etc/logrotate.d/audit")

def install_SELinux():
    '''
    Install SELinux policies for logrotate of audit logs.
    See .te files for policy details.
    '''

    # Create a local dir for SELinux modules
    x("mkdir -p /var/lib/syco_selinux_modules/server")
    module_path = "{0}var/logrotate/SELinux_modules".format(app.SYCO_PATH)
    x("cp {0}/*.pp /var/lib/syco_selinux_modules/server".format(module_path))
    x("semodule -i /var/lib/syco_selinux_modules/server/logrotate*.pp")
