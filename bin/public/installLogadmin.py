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

import os
import string
import mysqlUtils

from general import x
from scopen import scOpen
from general import deploy_web, remove_web
import app
import config
import iptables
import version
import installHttpd

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1





def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-logadmin",   install_logadmin,   help="Install Log managemenet tools.")
    commands.add("uninstall-logadmin", uninstall_logadmin, help="Uninstall Log managemenet tools.")


def install_logadmin(args):
    x("yum install httpd -y")
    deploy_web('Logadmin','/opt/syco/var/logadmin/www/','/opt/syco/var/logadmin/httpd/vhost.conf')
    _configure_apache()

    sql_password = general.generate_password(20, string.letters + string.digits)
    _create_db_user(sql_password)
    x("mysql Syslog --user='{0}' --password='{1}' < /opt/syco/var/logadmin/httpd/mysql.sql".format("icinga",re.escape(sqlpassword)))


    logConfig = scOpen("/var/www/html/Logadmin/log_mysql.py")
    logConfig.replace("${MYSQL_PASSWORD}", sql_password)



def uninstall_logadmin(args):
    remove_web('Logadmin')

def _configure_apache():
    '''
    Add conf.d files to apache for loganalyzer

    '''
    htconf = scOpen("/etc/httpd/conf.d/Logadmin.conf")
    htconf.replace("${BIND_DN}","cn=sssd,{0}".format(
        config.general.get_ldap_dn()
    ))
    htconf.replace("${BIND_PASSWORD}", app.get_ldap_sssd_password())
    htconf.replace("${LDAP_URL}", "ldaps://{0}:636/{1}?uid".format(
        config.general.get_ldap_hostname(), config.general.get_ldap_dn()
    ))

    x("service httpd restart")


def _configure_loagadmin():
	'''
	Configure logadmin user and password
	'''


def _create_db_user(sql_password):
    '''
    Create db user for loganalyzer.

    ryslogd and loganalyzer has it's own user.

    Note: Granting all privileges, fewer is possible.

    '''
    mysqlUtils.drop_user('logadmin')
    mysqlUtils.create_user('logadmin', sql_password, 'Syslog')