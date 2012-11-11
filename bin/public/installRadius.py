#!/usr/bin/env python
'''
Install FreeRadius.

TESTING
To test that radious works run this command.

    $ radtest ldap_username ldap_password localhost 0 testing123

READ MORE
www.freeradius.org

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
import re

from general import x, use_original_file
from scopen import scOpen
import app
import config
import iptables
import version


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-radius",   install_freeradius,   help="Install FreeRadius server on the current server.")
    commands.add("uninstall-radius", uninstall_freeradius, help="Uninstall Freeradius server on the current server.")


def install_freeradius(args):
    '''
    Install and configure the freeradius on the local host.

    '''
    app.print_verbose("Install FreeRadius version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallFreeRadius", SCRIPT_VERSION)
    version_obj.check_executed()

    # Initialize all passwords used by the script
    app.get_ldap_admin_password()

    _install_packages()

    # Configure iptables
    iptables.add_freeradius_chain()
    iptables.save()

    _configure_ldap()
    _enable_ldap()

    x("/etc/init.d/radiusd restart")

    version_obj.mark_executed()


def _install_packages():
    '''
    Install required packages.
    '''
    if (not os.access("/usr/sbin/radiusd", os.W_OK|os.X_OK)):
        x("yum -y install freeradius-utils freeradius-ldap")

        x("/sbin/chkconfig radiusd on ")
        if (not os.access("/usr/sbin/radiusd", os.F_OK)):
            raise Exception("Couldn't install FreeRadius")


def _configure_ldap():
    app.print_verbose("Copying config")

    use_original_file("/etc/raddb/modules/ldap")

    # General ldap setup.
    ldapconf = scOpen("/etc/raddb/modules/ldap")
    ldapconf.replace(
        '\\t*server =.*',
        '\\tserver="ldaps://{0}"'.format(
            config.general.get_ldap_hostname()
        )
    )
    ldapconf.replace(
        '\\t#identity = .*',
        '\\tidentity = "cn=sssd,{0}"'.format(
            config.general.get_ldap_dn()
        )
    )
    ldapconf.replace(
        '\\t#password = .*',
        '\\tpassword = "{0}"'.format(
            re.escape(app.get_ldap_sssd_password())
        )
    )
    ldapconf.replace(
        '\\tbasedn = .*',
        '\\tbasedn ="{0}"'.format(
            config.general.get_ldap_dn()
        )
    )
    ldapconf.replace(
        '\\tfilter = .*',
        '\\tfilter ="(uid=%u)"'
    )
    ldapconf.replace(
        '\\t#base_filter = .*',
        '\\tbase_filter = "(employeeType=Sysop)"'
    )

    # Deal with certs
    ldapconf.replace(
        '\\t\\t# cacertfile.*=.*',
        '\\t\\tcacertfile\\t= /etc/openldap/cacerts/ca.crt'
    )
    ldapconf.replace(
        '\\t\\t# certfile.*=.*',
        '\\t\\tcertfile\\t= /etc/openldap/cacerts/client.crt'
    )
    ldapconf.replace(
        '\\t\\t# keyfile.*=.*',
        '\\t\\tkeyfile\\t= /etc/openldap/cacerts/client.key'
    )


def _enable_ldap():
    '''
    Enable ldap auth.

    '''
    use_original_file("/etc/raddb/sites-enabled/default")
    # Replace first occurance of "#\tldap" with "\tldap"
    x("/usr/bin/awk '/^[#]\\tldap/{c++;if(c==1){sub(\"^[#]\\tldap\",\"\\tldap\")}}1' %s" %
        "/etc/raddb/sites-enabled/default > /etc/raddb/sites-enabled/default.tmp"
    )
    x("cp -f /etc/raddb/sites-enabled/default.tmp /etc/raddb/sites-enabled/default")
    x("rm -f /etc/raddb/sites-enabled/default.tmp")


def uninstall_freeradius(args):
    '''
    Uninstall freeradius

    '''
    if (os.access("/etc/init.d/radiusd", os.F_OK)):
        x("/etc/init.d/radiusd stop")
    x("yum -y remove freeradius freeradius-utils freeradius-ldap")
    x("rm -rf /etc/raddb")

    version_obj = version.Version("InstallFreeRadius", SCRIPT_VERSION)
    version_obj.mark_uninstalled()

