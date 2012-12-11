#!/usr/bin/env python
'''
Install and configure adiscon.com loganalyzer.

It connects to the rsyslogd mysql database.

READ MORE
http://loganalyzer.adiscon.com/

'''

__author__ = "daniel@cybercow.se, anders@televerket.net"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import mysqlUtils
import os
import string

from general import x
from scopen import scOpen
import app
import config
import general
import install
import installHttpd
import iptables
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


# Download of loganalyzer
LOGANALYZER_FILE = "loganalyzer-3.5.6"
LOGANALYZER_URL = "http://download.adiscon.com/loganalyzer/{0}.tar.gz".format(LOGANALYZER_FILE)


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-loganalyzer",   install_loganalyzer,   help="Install Log managemenet tools.")
    commands.add("uninstall-loganalyzer", uninstall_loganalyzer, help="Uninstall Log managemenet tools.")


def install_loganalyzer(args):
    '''
    Install and configure adiscon.com loganalyzer.

    '''
    app.print_verbose("Install loganalyzer version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallLoganalyzer", SCRIPT_VERSION)
    version_obj.check_executed()

    # Initialize all passwords used by the script
    app.init_mysql_passwords()

    _install_packages(args)
    _download_loganalyzer()

    sql_password = general.generate_password(20, string.letters + string.digits)
    _create_db_user(sql_password)
    _configure_loganalyzer(sql_password)

    _configure_apache()
    _set_permissions()

    version_obj.mark_executed()


def _install_packages(args):
    '''
    Install depencency packages.

    '''
    if not os.path.exists('/etc/init.d/httpd'):
        installHttpd.install_httpd(args)

    if not install.is_rpm_installed('php'):
        x("yum -y install php php-mysql php-gd")


def _download_loganalyzer():
    '''
    Download loganalyzer tar.gz and extract files in httpd folder.

    '''
    # Remove old installation
    x("rm -rf /var/www/html/loganalyzer")

    general.download_file(LOGANALYZER_URL)
    x("tar zxf {0}/{1}.tar.gz -C {2}".format(
        app.INSTALL_DIR, LOGANALYZER_FILE, app.INSTALL_DIR)
    )
    x("cp -rp /{0}/{1}/src /var/www/html/loganalyzer".format(
        app.INSTALL_DIR, LOGANALYZER_FILE
    ))


def _create_db_user(sql_password):
    '''
    Create db user for loganalyzer.

    ryslogd and loganalyzer has it's own user.

    Note: Granting all privileges, fewer is possible.

    '''
    mysqlUtils.drop_user('loganalyzer')
    mysqlUtils.create_user('loganalyzer', sql_password, 'Syslog')


def _configure_loganalyzer(sql_password):
    '''
    Setup loganalyzers config file.

    The config file is created with the installation tool provided with
    loganalyzer. But that tools is hard to automatically install, so
    prepared config file is instead copied.

    Note: When upgrading loganalyzer it might require a new config.php file.

    '''
    x("cp -f {0}var/loganalyzer/config.php /var/www/html/loganalyzer/".format(
        app.SYCO_PATH)
    )
    logConfig = scOpen("/var/www/html/loganalyzer/config.php")
    logConfig.replace("${MYSQL_PASSWORD}", sql_password)


def _configure_apache():
    '''
    Add conf.d files to apache for loganalyzer

    '''
    x("cp -f {0}var/loganalyzer/loganalyzer.conf /etc/httpd/conf.d/".format(
        app.SYCO_PATH
    ))
    htconf = scOpen("/etc/httpd/conf.d/loganalyzer.conf")
    htconf.replace("${BIND_DN}","cn=sssd,{0}".format(
        config.general.get_ldap_dn()
    ))
    htconf.replace("${BIND_PASSWORD}", app.get_ldap_sssd_password())
    htconf.replace("${LDAP_URL}", "ldaps://{0}:636/{1}?uid".format(
        config.general.get_ldap_hostname(), config.general.get_ldap_dn()
    ))

    x("service httpd restart")


def _set_permissions():
    '''
    Set permissions for all installed files.

    '''
    x("chown -R apache:apache /var/www/html/loganalyzer")
    x("restorecon -R /var/www/html/loganalyzer")
    x("/usr/sbin/setsebool -P httpd_can_network_connect=1")


def uninstall_loganalyzer(args):
    '''
    Uninstall loganalyzer.

    '''
    x("yum -y erase php php-mysql php-gd")

    # Depencencies
    x("yum -y erase apr apr-util apr-util-ldap freetype httpd httpd-tools libX11 libX11-common libXau libXpm libjpeg libpng libxcb mailcap php-cli php-common php-pdo ")

    # Files that was used.
    x("rm -rf /var/www/html/loganalyzer")
    x("rm /etc/httpd/conf.d/loganalyzer.conf")

    #
    version_obj = version.Version("InstallLoganalyzer", SCRIPT_VERSION)
    version_obj.mark_uninstalled()

