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
import app, config
from app import SYCO_PATH, SYCO_ETC_PATH, SYCO_USR_PATH, SYCO_VAR_PATH
from general import x
import version

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

    # Override base repo to one that works
    x("cat %syum/CentOS-Base.repo > /etc/yum.repos.d/CentOS-Base.repo" % app.SYCO_VAR_PATH)

    # Run all yum updates through proxy if available
    proxy_host = config.general.get_proxy_host()
    proxy_port = config.general.get_proxy_port()
    if proxy_host and proxy_port:
        x('echo http_proxy=%s >> /etc/yum.conf' % "http://%s:%s" % (proxy_host,proxy_port))

    #Set Swappiness to 0 on all hosts to avoid excessive swapping
    x('sysctl vm.swappiness=0')

    app.print_verbose("Install required packages for syco")
    x("yum install augeas -y")

    app.print_verbose("Create symlink /sbin/syco")
    set_syco_permissions()
    if not os.path.exists('/sbin/syco'):
        os.symlink('%sbin/syco.py' % SYCO_PATH, '/sbin/syco')

    # Use augeas to set max kernels to 2 since more won't fit on /boot
    from augeas import Augeas
    augeas = Augeas(x)
    augeas.set_enhanced("/files/etc/yum.conf/main/installonly_limit", "2")

    if proxy_host and proxy_port:
        # Set proxy again with augeas to ensure there are no duplicates/inconsistencies
        augeas.set_enhanced("/files/etc/yum.conf/main/proxy", "http://%s:%s" % (proxy_host,proxy_port))


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
    print "get_root_password:", app.get_root_password()
    print "get_root_password_hash:", app.get_root_password_hash()
    print "get_ca_password:", app.get_ca_password()
    print "get_glassfish_admin_password:", app.get_glassfish_admin_password()
    print "get_glassfish_master_password:", app.get_glassfish_master_password()
    print "get_haproxy_sps_ping_password:", app.get_haproxy_sps_ping_password()
    print "get_ldap_admin_password:", app.get_ldap_admin_password()
    print "get_ldap_sssd_password:", app.get_ldap_sssd_password()
    print "get_master_password:", app.get_master_password()
    print "get_mysql_backup_password:", app.get_mysql_backup_password()
    print "get_mysql_integration_password:", app.get_mysql_integration_password()
    print "get_mysql_monitor_password:", app.get_mysql_monitor_password()
    print "get_mysql_production_password:", app.get_mysql_production_password()
    print "get_mysql_root_password:", app.get_mysql_root_password()
    print "get_mysql_stable_password:", app.get_mysql_stable_password()
    print "get_mysql_uat_password:", app.get_mysql_uat_password()
    print "get_redis_production_password:", app.get_redis_production_password()
    print "get_svn_password:", app.get_svn_password()
    print "get_switch_icmp_password:", app.get_switch_icmp_password()


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
