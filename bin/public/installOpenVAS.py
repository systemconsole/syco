#!/usr/bin/env python
'''
Install OpenVAS.

READ MORE
http://openvas.org

'''

__author__ = "daniel.lindh@cybercow.se, anders@televerket.net"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import  os

from general import x, get_install_dir
from scopen import scOpen
import install
import app
import config
import general
import iptables
import version


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("install-openvas",   install_openvas,   help="Install OpenVAS.")
    commands.add("uninstall-openvas", uninstall_openvas, help="Uninstall NMAP.")


def install_openvas(args):
    '''
    Install and configure openvas on the local host.

    '''
    app.print_verbose("Install OpenVAS version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallOpenVAS", SCRIPT_VERSION)
    version_obj.check_executed()

    _install_packages()
    _disable_selinux()

    iptables.add_openvas_chain()
    iptables.save()

    #
    app.print_verbose("Get OpenVAS nvt.")
    x("openvas-nvt-sync --wget &> /dev/null ")

    #
    app.print_verbose("Rebuild OpenVAS database.")
    x("openvasmd --rebuild")

    #
    app.print_verbose("Add default OpenVAS admin user.")
    x("openvasad -c 'add_user' -u admin -w admin --role=Admin")

    _modify_configs()
    _setup_default_database()
    _start_all_services()

    version_obj.mark_executed()


def _install_packages():
    '''
    Install all required packages and repositories.

    '''
    install.atomic_repo()
    install.package("sqlite")
    install.package("openvas")


def _disable_selinux():
    '''
    Disable selinux

    '''
    app.print_verbose("Disabling SELinux")
    x("echo 0 > /selinux/enforce")
    selinuxconf = scOpen("/etc/selinux/config")
    selinuxconf.replace("^SELINUX=.*","SELINUX=permissive")


def _modify_configs():
    '''
    Modify openvas config files.

    '''
    app.print_verbose('Modify config.')
    general.use_original_file("/etc/sysconfig/gsad")
    gsadconf = scOpen("/etc/sysconfig/gsad")
    gsadconf.replace("^GSA_ADDRESS=127\.0\.0\.1", "GSA_ADDRESS=0\.0\.0\.0")
    gsadconf.replace("^#GSA_SSL_PRIVATE_KEY=", "GSA_SSL_PRIVATE_KEY=/var/lib/openvas/private/CA/serverkey.pem")
    gsadconf.replace("^#GSA_SSL_CERTIFICATE=", "GSA_SSL_CERTIFICATE=/var/lib/openvas/CA/servercert.pem")


def _setup_default_database():
    '''
    Create sqllite default database for openvas.

    Sql file is a dumpo of the database after reqular openvas installation.

    '''
    app.print_verbose('Setup default database')
    x("cp -f {0}var/openvas/sql_init.sql {1}sql_init.sql".format(
        app.SYCO_PATH, get_install_dir()
    ))

    sql = scOpen("{0}sql_init.sql".format(get_install_dir()))
    sql.replace("${SYCO_HOSTS}", config.general.get_subnet())
    sql.replace("${SYCO_ALERT_EMAIL}",config.general.get_admin_email())
    x("cat {0}sql_init.sql | sqlite3 /var/lib/openvas/mgr/tasks.db".format(
        get_install_dir()
    ))


def _start_all_services():
    '''
    Start all deamons and set for autostart at boot time.

    '''
    x("/etc/init.d/openvas-manager restart")
    x("/etc/init.d/openvas-administrator restart")
    x("/etc/init.d/openvas-scanner restart")
    x("/etc/init.d/gsad restart")

    x("chkconfig openvas-manager on")
    x("chkconfig openvas-administrator on")
    x("chkconfig openvas-scanner on")
    x("chkconfig gsad on")


def uninstall_openvas(args):
    '''
    Uninstall openvas

    '''
    if (os.access("/etc/init.d/openvas-manager", os.F_OK)):
        app.print_verbose("Stop all services.")
        x("/etc/init.d/openvas-manager stop")
        x("/etc/init.d/openvas-scanner stop")
        x("/etc/init.d/gsad stop")

    #
    app.print_verbose("Remove packages and files.")
    x("yum -y remove openvas-*")
    x("rm -rf /var/lib/openvas")
    x("rm /etc/yum.repos.d/atomic.repo")

    #
    app.print_verbose("Remove iptables rules.")
    iptables.del_openvas_chain()
    iptables.save()

    #
    app.print_verbose("Enabling SELINUX.")
    x("echo 1 > /selinux/enforce")
    selinuxconf = scOpen("/etc/selinux/config")
    selinuxconf.replace("^SELINUX=.*","SELINUX=enforcing")

    #
    app.print_verbose("Tell syco openvas is uninstalled.")
    version_obj = version.Version("InstallOpenVAS", SCRIPT_VERSION)
    version_obj.mark_uninstalled()
