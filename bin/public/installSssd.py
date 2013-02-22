#!/usr/bin/env python
'''
Install sssd that will connect to an LDAP-server.

This script can be executed on both the LDAP-server and it's clients.

This script is based on information from at least the following links.
  http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=2
  http://docs.fedoraproject.org/en-US/Fedora/15/html/Deployment_Guide/chap-SSSD_User_Guide-Introduction.html
  http://directory.fedoraproject.org/wiki/Howto:PAM

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

import app
import config
import general
from general import x
from general import shell_run
from scopen import scOpen
import iptables
import version
import installOpenLdap

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("install-sssd-client", install_sssd, help="Install sssd (ldap client).")
    commands.add("uninstall-sssd-client", uninstall_sssd, help="Uninstall sssd.")

def install_sssd(args):
    '''
    Install ldap client on current host and connect to networks ldap server.

    '''
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
    configured_sssd()
    configured_sudo()

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
    x("yum -y install openldap openldap-clients authconfig pam_ldap sssd")

def download_cert(filename):
    '''
    Get certificate from ldap server.

    This is not needed to be done on the server.

    '''
    #Creating certs folder
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
    '''
    Get certificate from ldap server

    This is not needed to be done on the server.

    '''
    download_cert("client.pem")
    download_cert("ca.crt")
    installOpenLdap.set_permissions_on_certs()

def authconfig():
    '''
    Configure all relevant /etc files for sssd, ldap etc.

    '''
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
    x(cmd % (
            config.general.get_ldap_hostname(),
            config.general.get_ldap_dn()
        )
    )

def configured_sssd():
    # If the authentication provider is offline, specifies for how long to allow
    # cached log-ins (in days). This value is measured from the last successful
    # online log-in. If not specified, defaults to 0 (no limit).
    scOpen("/etc/sssd/sssd.conf").remove("^offline_credentials_expiration.*")
    x("sed -i '/\[pam\]/a offline_credentials_expiration=5' /etc/sssd/sssd.conf")

    # Enumeration means that the entire set of available users and groups on the
    # remote source is cached on the local machine. When enumeration is disabled,
    # users and groups are only cached as they are requested.
    scOpen("/etc/sssd/sssd.conf").remove("^enumerate=true")
    scOpen("/etc/sssd/sssd.conf").replace("\[domain/default\]","\[domain/default\]\nenumerate=true")

    # Configure client certificate auth.
    scOpen("/etc/sssd/sssd.conf").remove("^ldap_tls_cert.*")
    scOpen("/etc/sssd/sssd.conf").remove("^ldap_tls_key.*")
    scOpen("/etc/sssd/sssd.conf").remove("^ldap_tls_reqcert.*")
    scOpen("/etc/sssd/sssd.conf").replace("\[domain/default\]",
        "\[domain/default\]\n" +
        "ldap_tls_cert = /etc/openldap/cacerts/client.pem\n" +
        "ldap_tls_key = /etc/openldap/cacerts/client.pem\n" +
        "ldap_tls_reqcert = demand"
    )

    # Only users with this employeeType are allowed to login to this computer.
    scOpen("/etc/sssd/sssd.conf").remove("^access_provider.*")
    scOpen("/etc/sssd/sssd.conf").remove("^ldap_access_filter.*")
    scOpen("/etc/sssd/sssd.conf").replace("\[domain/default\]",
        "\[domain/default\]\n" +
        "access_provider = ldap\n" +
        "ldap_access_filter = (employeeType=Sysop)"
    )

    # Login to ldap with a specified user.
    scOpen("/etc/sssd/sssd.conf").remove("^ldap_default_bind_dn.*")
    scOpen("/etc/sssd/sssd.conf").remove("^ldap_default_authtok_type.*")
    scOpen("/etc/sssd/sssd.conf").remove("^ldap_default_authtok.*")
    scOpen("/etc/sssd/sssd.conf").replace("\[domain/default\]",
        "\[domain/default\]\n" +
        "ldap_default_bind_dn = cn=sssd," + config.general.get_ldap_dn()
    )
    scOpen("/etc/sssd/sssd.conf").replace("\[domain/default\]",
        "\[domain/default\]\n" +
        "ldap_default_authtok_type = password"
    )
    scOpen("/etc/sssd/sssd.conf").replace("\[domain/default\]",
        "\[domain/default\]\n" +
        "ldap_default_authtok = " + app.get_ldap_sssd_password()
    )

    # Need to change the modified date before restarting, to tell sssd to reload
    # the config file.
    x("touch /etc/sssd/sssd.conf")

    # Restart sssd and read in all new configs.
    x("rm /var/lib/sss/db/config.ldb")
    x("service sssd restart")

    # Start sssd after reboot.
    x("chkconfig sssd on")

###########################################################
# Configure the client to use sudo
###########################################################
def configured_sudo():
    scOpen("/etc/nsswitch.conf").remove("^sudoers.*")
    scOpen("/etc/nsswitch.conf").add("sudoers: ldap files")

    x("touch /etc/ldap.conf")
    x("chown root:root /etc/ldap.conf")
    x("chmod 644 /etc/ldap.conf")
    scOpen("/etc/ldap.conf").remove(
        "^sudoers_base.*\|^binddn.*\|^bindpw.*\|^ssl.*\|^tls_cacertdir.*\|" +
        "^tls_cert.*\|^tls_key.*\|sudoers_debug.*"
    )
    scOpen("/etc/ldap.conf").add(
        "uri ldaps://" + config.general.get_ldap_hostname() + "\n" +
        "base " + config.general.get_ldap_dn() + "\n" +
        "ssl on\n" +
        "tls_cacertdir /etc/openldap/cacerts\n" +
        "tls_cert /etc/openldap/cacerts/client.pem\n" +
        "tls_key /etc/openldap/cacerts/client.pem\n" +
        "sudoers_base ou=SUDOers," + config.general.get_ldap_dn() + "\n" +
        "binddn cn=sssd," + config.general.get_ldap_dn() + "\n" +
        "bindpw " + app.get_ldap_sssd_password()
    )

    # SUDO now uses it's own ldap config file.
    x("cp /etc/ldap.conf /etc/sudo-ldap.conf")
    x("chmod 440 /etc/sudo-ldap.conf")
    x("chown root:root /etc/sudo-ldap.conf")
    x("restorecon /etc/sudo-ldap.conf")

    # Enable debugmode
    #scOpen("/etc/ldap.conf").add("sudoers_debug 5")

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
