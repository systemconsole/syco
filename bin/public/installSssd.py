#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Install sssd that will connect to an LDAP-server.

This script can be executed on both the LDAP-server and it's clients.

This script is based on information from at least the following links.
  http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=2
  http://docs.fedoraproject.org/en-US/Fedora/15/html/Deployment_Guide/chap-SSSD_User_Guide-Introduction.html
  http://directory.fedoraproject.org/wiki/Howto:PAM

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh, Kristofer Borgström"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import app
import config
import general
from augeas import Augeas
from general import x
from general import shell_run
import iptables
import version
import installOpenLdap

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


def build_commands(commands):
    commands.add("install-sssd-client", install_sssd, help="Install sssd.")
    commands.add("uninstall-sssd-client", uninstall_sssd, help="Uninstall sssd.")


def install_sssd(args):
    """
    Install ldap client on current host and connect to networks ldap server.

    """
    app.print_verbose("Install sssd script-version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallSssd", SCRIPT_VERSION)
    version_obj.check_executed()

    # Get all passwords from installation user at the start of the script.
    app.get_ldap_sssd_password()

    install_packages()

    installOpenLdap.setup_hosts()
    iptables.add_ldap_chain()
    iptables.save()

    ip = config.general.get_ldap_server_ip()
    general.wait_for_server_to_start(ip, "636")

    install_certs()

    # For some reason it needs to be executed twice.
    authconfig()
    authconfig()

    installOpenLdap.configure_client_cert_for_ldaptools()
    augeas = Augeas(x)
    configure_sssd(augeas)
    configure_sudo(augeas)

    version_obj.mark_executed()


def uninstall_sssd(args):
    app.print_verbose("Uninstall sssd script-version: %d" % SCRIPT_VERSION)
    x("yum -y remove openldap-clients sssd")
    x("rm -rf /var/lib/sss/")

    iptables.del_ldap_chain()
    iptables.save()

    version_obj = version.Version("InstallSssd", SCRIPT_VERSION)
    version_obj.mark_uninstalled()


def install_packages():
    x("yum -y install openldap openldap-clients authconfig pam_ldap sssd augeas")


def download_cert(filename):
    """
    Get certificate from ldap server.

    This is not needed to be done on the server.

    """
    # Creating certs folder
    x("mkdir -p /etc/openldap/cacerts")

    ip = config.general.get_ldap_server_ip()
    fullpath = '/etc/openldap/cacerts/' + filename
    shell_run("scp root@%s:%s %s" % (ip, fullpath, fullpath),
        events={
            'Are you sure you want to continue connecting \(yes\/no\)\?': "YES\n",
            "root@" + ip + "\'s password\:": app.get_root_password() + "\n"
        }
    )


def install_certs():
    """
    Get certificate from ldap server

    This is not needed to be done on the server.

    """
    download_cert("client.pem")
    download_cert("ca.crt")
    installOpenLdap.set_permissions_on_certs()


def authconfig():
    """
    Configure all relevant /etc files for sssd, ldap etc.

    """
    cmd = (
        "authconfig" +
        " --enablesssd --enablesssdauth --enablecachecreds" +
        " --enableldap --enableldaptls --enableldapauth" +
        " --ldapserver='ldaps://%s' --ldapbasedn='%s'" +
        " --disablenis --disablekrb5" +
        " --enableshadow --enablemkhomedir --enablelocauthorize" +
        " --passalgo=sha512" +
        " --updateall"
    )
    x(cmd %
        (
            config.general.get_ldap_hostname(),
            config.general.get_ldap_dn()
        )
    )


def configure_sssd(augeas):
    # If the authentication provider is offline, specifies for how long to allow
    # cached log-ins (in days). This value is measured from the last successful
    # online log-in. If not specified, defaults to 0 (no limit).
    # We want to cache credentials even though noone has logged in.
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'pam']/offline_credentials_expiration", "0")

    # Enumeration means that the entire set of available users and groups on the
    # remote source is cached on the local machine. When enumeration is disabled,
    # users and groups are only cached as they are requested.
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/enumerate", "true")

    # Configure client certificate auth.
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_tls_cert",
                        "/etc/openldap/cacerts/client.pem")
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_tls_key",
                        "/etc/openldap/cacerts/client.pem")
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_tls_reqcert", "demand")

    # Only users with this employeeType are allowed to login to this computer.
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/access_provider", "ldap")
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_access_filter",
                        "(employeeType=Sysop)")

    # Login to ldap with a specified user.
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_default_bind_dn",
                            "cn=sssd," + config.general.get_ldap_dn())
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_default_authtok_type", "password")
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_default_authtok",
                            app.get_ldap_sssd_password())

    # Enable caching of sudo rules
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/sudo_provider", "ldap")
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_sudo_full_refresh_interval",
                        "86400")
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_sudo_smart_refresh_interval",
                        "3600")

    # Set low timeout levels to ensure that cache is used when ldap is slow/down
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_search_timeout", "5")
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_enumeration_search_timeout", "5")
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'domain/default']/ldap_network_timeout", "5")

    # sssd section settings
    augeas.set_enhanced("/files/etc/sssd/sssd.conf/target[. = 'sssd']/services", "nss,pam,sudo")

    # Need to change the modified date before restarting, to tell sssd to reload
    # the config file.
    x("touch /etc/sssd/sssd.conf")

    # Restart sssd and read in all new configs.
    x("rm /var/lib/sss/db/config.ldb")
    x("service sssd restart")

    # Start sssd after reboot.
    x("chkconfig sssd on")


def configure_sudo(augeas):
    """
    Configure the client to use sudo

    """
    # The database sudoers node doesn't appear to be insertable with a
    # one liner so we have to echo it in
    if not augeas.find_entry("/files/etc/nsswitch.conf/database[. = 'sudoers']"):
        x("echo \"sudoers: files sss\" >> /etc/nsswitch.conf")
    else:
        augeas.set_enhanced("/files/etc/nsswitch.conf/database[. = 'sudoers']/service[1]", "files")
        augeas.set_enhanced("/files/etc/nsswitch.conf/database[. = 'sudoers']/service[2]", "sss")
        augeas.remove("/files/etc/nsswitch.conf/database[. = 'sudoers']/service[3]")

    x("touch /etc/ldap.conf")
    x("chown root:root /etc/ldap.conf")
    x("chmod 644 /etc/ldap.conf")

    augeas.set_enhanced("/files/etc/ldap.conf/uri", "ldaps://%s" % config.general.get_ldap_hostname())
    augeas.set_enhanced("/files/etc/ldap.conf/base",  config.general.get_ldap_dn())
    augeas.set_enhanced("/files/etc/ldap.conf/ssl",  "on")
    augeas.set_enhanced("/files/etc/ldap.conf/tls_cacertdir", "/etc/openldap/cacerts")
    augeas.set_enhanced("/files/etc/ldap.conf/tls_cert", "/etc/openldap/cacerts/client.pem")
    augeas.set_enhanced("/files/etc/ldap.conf/tls_key", "/etc/openldap/cacerts/client.pem")
    augeas.set_enhanced("/files/etc/ldap.conf/sudoers_base", "ou=SUDOers,dc=fareoffice,dc=com")
    augeas.set_enhanced("/files/etc/ldap.conf/binddn", "cn=sssd,%s" % config.general.get_ldap_dn())
    augeas.set_enhanced("/files/etc/ldap.conf/bindpw", app.get_ldap_sssd_password())

    # SUDO now uses it's own ldap config file. But some applications don't.
    x("cp /etc/ldap.conf /etc/sudo-ldap.conf")
    x("chmod 440 /etc/sudo-ldap.conf")
    x("chown root:root /etc/sudo-ldap.conf")
    x("restorecon /etc/sudo-ldap.conf")

    # Enable debug mode
    # scOpen("/etc/ldap.conf").add("sudoers_debug 5")

###########################################################
# Test to see that everything works fine.
###########################################################

# Should return everything.
# ldapsearch -b dc=fareoffice,dc=com -D "cn=Manager,dc=fareoffice,dc=com" -w secret
# ldapsearch -b dc=fareoffice,dc=com -D "cn=Manager,dc=fareoffice,dc=com" -w secret

# Return my self.
# ldapsearch -b uid=danlin,ou=people,dc=fareoffice,dc=com -D "uid=danlin,ou=people,dc=fareoffice,dc=com" -w fratsecret

# Can't access somebody else
# ldapsearch -b uid=user3,ou=people,dc=fareoffice,dc=com -D "uid=user4,ou=people,dc=fareoffice,dc=com" -w fratsecret

# Should return nothing.
# ldapsearch -b dc=fareoffice,dc=com -D ""

# Return sudo info
# ldapsearch -b ou=SUDOers,dc=fareoffice,dc=com -D "cn=sssd,dc=fareoffice,dc=com" -w secret

# Test sssd
# getent passwd
# getent group

# Test if sudo is using LDAP.
# sudo -l
