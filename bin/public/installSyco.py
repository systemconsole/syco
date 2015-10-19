#!/usr/bin/env python
"""
Install and configure syco to be used on localhost.

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os, sys, os.path
import app
from app import SYCO_PATH, SYCO_ETC_PATH, SYCO_USR_PATH, SYCO_VAR_PATH
from general import x
import version
from augeas import Augeas

# The version of this module, used to prevent the same script version to be 
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    commands.add("install-syco", install_syco, help="Install the syco script on the current server.")
    commands.add("passwords",    passwords, help="Set all passwords used by syco.")
    commands.add("change-env",   change_env, "[env]", help="Set syco environment.")


def install_syco(args):
    """
    Install/configure this script on the current computer.

    """
    app.print_verbose("Install syco version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallSYCO", SCRIPT_VERSION)
    version_obj.check_executed()

    app.print_verbose("Install required packages for syco")
    x("yum install pexpect python-crypto augeas -y")

    app.print_verbose("Create symlink /sbin/syco")
    set_syco_permissions()
    if not os.path.exists('/sbin/syco'):
        os.symlink('%sbin/syco.py' % SYCO_PATH, '/sbin/syco')
    x("cat %syum/CentOS-Base.repo > /etc/yum.repos.d/CentOS-Base.repo" % app.SYCO_VAR_PATH)

    #Use augeas to set max kernels to 2 since more won't fit on /boot
    from augeas import Augeas
    augeas = Augeas(x)
    augeas.set_enhanced("/files/etc/yum.conf/main/installonly_limit", "2")

    version_obj.mark_executed()


def set_syco_permissions():
    """Set permissions on all syco files"""
    x("chmod 0750 /opt/syco")
    x("chmod 0750 /opt/syco/var")
    x("chmod 0750 /opt/syco/var/mysql")
    x("chmod 0750 /opt/syco/var/mysql/mysql-lvm-backup.py")
    x("chmod 0750 /opt/syco/var/mysql/mysqldump-backup.sh")


def passwords(args):
    app.print_verbose("Set all passwords used by syco")
    app.init_all_passwords()
    print "root: ", app.get_root_password()
    print "svn: ", app.get_svn_password()
    print "ldap_admin: ", app.get_ldap_admin_password()
    print "ldap_sssd: ", app.get_ldap_sssd_password()
    print "glassfish_master: ", app.get_glassfish_master_password()
    print "glassfish_admin: ", app.get_glassfish_admin_password()
    print "glassfish_user: ", app.get_user_password("glassfish")
    print "mysql_root: ", app.get_mysql_root_password()
    print "mysql_int: ", app.get_mysql_integration_password()
    print "mysql_stable: ", app.get_mysql_stable_password()
    print "mysql_uat: ", app.get_mysql_uat_password()
    print "mysql_prod: ", app.get_mysql_production_password()
    print "mysql_backup: ",app.get_mysql_backup_password()
    print "mysql_monitor: ",app.get_mysql_monitor_password()
    print "switch_icmp: ",app.get_switch_icmp_password()


def change_env(args):
    """
    Change syco invironment files.

    passwordstore and install.cfg files are relinked.

    """
    if (len(args) != 2):
        raise Exception("syco chagne-env [env]")

    env = args[1]

    app.print_verbose("Change to env " + env)
    x("rm %spasswordstore " % (SYCO_ETC_PATH))
    x("ln -s %spasswordstore.%s %spasswordstore" % (
        SYCO_ETC_PATH, env, SYCO_ETC_PATH)
      )

    if (os.access(app.SYCO_USR_PATH, os.F_OK)):
        for plugin in os.listdir(app.SYCO_USR_PATH):
            plugin_path = os.path.abspath(app.SYCO_USR_PATH + plugin + "/etc/")

            x("rm %s/install.cfg " % (plugin_path))
            x("ln -s %s/install-%s.cfg %s/install.cfg" % (plugin_path, env, plugin_path))
