#!/usr/bin/env python
'''
Install openldap-server.

This script is based on information from at least the following links.
    http://www.openldap.org/doc/admin24/guide.html
    https://help.ubuntu.com/10.04/serverguide/C/openldap-server.html
    http://home.roadrunner.com/~computertaijutsu/ldap.html
    http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=3
    http://www.server-world.info/en/note?os=CentOS_6&p=ldap
    http://linux.die.net/man/5/slapd-config
    http://eatingsecurity.blogspot.com/2008/11/openldap-security.html
    http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/ch-Directory_Servers.html#s1-OpenLDAP
    http://www.howtoforge.com/linux_ldap_authentication

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "2.0.0"
__status__ = "Production"

import os
import re
from types import ListType

import app
import config
from general import x
from scopen import scOpen
import iptables
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2

def build_commands(commands):
    commands.add("install-openldap", install_openldap, help="Install openldap.")
    commands.add("uninstall-openldap", uninstall_openldap, help="Uninstall openldap.")

def install_openldap(args):
    '''
    Install openldap on current host.

    '''
    app.print_verbose("Install openldap script-version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallOpenLdap", SCRIPT_VERSION)
    version_obj.check_executed()

    initialize_passwords()

    # Do the installation.
    enable_selinux()
    install_packages()
    store_logs_on_file()
    configure_ldap_client()
    configure_openldap()
    configure_sudo_in_ldap()
    create_modules()
    add_auditlog_overlay()
    add_pwdpolicy_overlay()
    add_user_domain()
    create_certs()
    enable_ssl()
    require_highest_security_from_clients()

    # Let clients connect to the server through the firewall. This is done after
    # everything else is done, so we are sure that the server is secure before
    # letting somebody in.
    iptables.add_ldap_chain()
    iptables.save()

    version_obj.mark_executed()

def uninstall_openldap(args):
    '''
    Uninstall openldap.

    '''
    app.print_verbose("Uninstall openldap script-version: %d" % SCRIPT_VERSION)
    x("service slapd stop")
    x("yum -y remove openldap-servers openldap-clients")

    x("rm -f /etc/openldap/cacerts/*")
    x("rm -rf /etc/openldap/schema")
    x("rm -f /etc/openldap/slapd.conf.bak")
    x("rm -rf /etc/openldap/slapd.d")
    x("rm -rf /var/lib/ldap")

    # Remove client cert configs
    scOpen("/etc/profile").remove(
        "^LDAPTLS_CERT.*\|^LDAPTLS_KEY.*\|export LDAPTLS_CERT LDAPTLS_KEY.*"
    )

    # Remove sudo configs.
    scOpen("/etc/nsswitch.conf").remove("^sudoers.*")
    scOpen("/etc/ldap.conf").remove(
        "^sudoers_base.*\|^binddn.*\|^bindpw.*\|^ssl on.*\|^tls_cert.*\|^tls_key.*\|sudoers_debug.*"
    )

    # Host information
    scOpen("/etc/hosts").remove('^' + config.general.get_ldap_server_ip() + ".*")

    #Remove logs
    x("rm -rf /var/log/slapd")

    iptables.del_ldap_chain()
    iptables.save()

    version_obj = version.Version("InstallOpenLdap", SCRIPT_VERSION)
    version_obj.mark_uninstalled()

def initialize_passwords():
    '''
    Get all passwords from installation user at the start of the script.

    '''
    app.get_ca_password()
    app.get_ldap_admin_password()
    app.get_ldap_sssd_password()

def enable_selinux():
    '''
    Enable SELinux for higher security.

    '''
    x("setenforce 1")
    x("setsebool -P domain_kernel_load_modules 1")

def install_packages():
    '''
    Install packages and start service.

    '''
    setup_hosts()

    # Install all required packages.
    x("yum -y install openldap-servers openldap-clients mlocate")

    # Create backend database.
    scOpen("/var/lib/ldap/DB_CONFIG").add(
        "set_cachesize 0 268435456 1\n" +
        "set_lg_regionmax 262144\n" +
        "set_lg_bsize 2097152"
    )
    x("chown -R ldap:ldap /var/lib/ldap")

    # Set password for cn=config (it's secret)
    scOpen('/etc/openldap/slapd.d/cn\=config/olcDatabase\=\{0\}config.ldif').add(
        'olcRootPW: %(ldap_password)s' %
        {'ldap_password': get_hashed_password(app.get_ldap_admin_password())}
    )

    # Autostart slapd after reboot.
    x("chkconfig slapd on")

    # Start ldap server
    x("service slapd start")

def store_logs_on_file():
    '''
    Store all openldap logs on file.

    '''
    # Create folder to store log files in
    x("mkdir /var/log/slapd")
    x("chmod 755 /var/log/slapd")
    x("chown ldap:ldap /var/log/slapd")

    # Redirect all log files through rsyslog to file.
    scOpen('/etc/rsyslog.conf').remove('local4.*')
    scOpen('/etc/rsyslog.conf').add(
        'local4.*                                                /var/log/slapd/slapd.log'
    )
    x("service rsyslog restart")

def configure_ldap_client():
    scOpen("/etc/openldap/ldap.conf").add(
	"uri ldaps://" + config.general.get_ldap_hostname() + "\n" +
	"base " + config.general.get_ldap_dn() + "\n" +
        "tls_cacertdir /etc/openldap/cacerts\n" +
        "tls_cert /etc/openldap/cacerts/client.pem\n" +
	"tls_key /etc/openldap/cacerts/client.pem\n" 
    )


def configure_openldap():
    '''
    General configuration of cn=config like passwords and access rights.

    '''
    # Ensure that openldap got time to start.
    x("sleep 1")

    # Do the configurations.
    ldapadd("admin", """
# Setup what to log.
dn: cn=config
changetype:modify
replace: olcLogLevel
olcLogLevel: 0
-
replace: olcIdleTimeout
olcIdleTimeout: 30

# Set access for the monitor db.
dn: olcDatabase={1}monitor,cn=config
changetype: modify
replace: olcAccess
olcAccess: {0}to * by dn.base="cn=Manager,%(dn)s" read by * none

# Set password for cn=config
dn: olcDatabase={0}config,cn=config
changetype: modify
replace: olcRootPW
olcRootPW: %(password)s

# Change LDAP-domain, password and access rights.
dn: olcDatabase={2}bdb,cn=config
changetype: modify
replace: olcSuffix
olcSuffix: %(dn)s
-
replace: olcRootDN
olcRootDN: cn=Manager,%(dn)s
-
replace: olcRootPW
olcRootPW: %(password)s
-
replace: olcAccess
olcAccess: {0}to attrs=employeeType by dn="cn=sssd,%(dn)s" read by self read by * none
olcAccess: {1}to attrs=userPassword,shadowLastChange by self write by anonymous auth by * none
olcAccess: {2}to dn.base="" by * none
olcAccess: {3}to * by dn="cn=config" write by dn="cn=sssd,%(dn)s" read by self write by * none
""" % {
    "dn": config.general.get_ldap_dn(),
    "password": get_hashed_password(app.get_ldap_admin_password())
    }
)

def configure_sudo_in_ldap():
    '''
    Configure sudo in ldap

    Users that should have sudo rights, are configured in the ldap-db. The ldap
    sudo schema are not configured by default, and are here created.

    Learn more:
        http://eatingsecurity.blogspot.com/2008/10/openldap-continued.html
        http://www.sudo.ws/sudo/man/1.8.2/sudoers.ldap.man.html

    '''
    # Update the locate database
    x('updatedb')

    # Copy the sudo Schema into the LDAP schema repository
    filepath = x('locate /usr/share/doc/*/schema.OpenLDAP').strip()
    x("/bin/cp -f %s /etc/openldap/schema/sudo.schema" % filepath)
    x("restorecon /etc/openldap/schema/sudo.schema")

    # Create a conversion file for the schema.
    x("mkdir /tmp/sudoWork")
    x("echo 'include /etc/openldap/schema/sudo.schema' > /tmp/sudoWork/sudoSchema.conf")

    # Convert the "Schema" to "LDIF".
    x("slapcat -f /tmp/sudoWork/sudoSchema.conf -F /tmp/ -n0 -s 'cn={0}sudo,cn=schema,cn=config' > /tmp/sudoWork/sudo.ldif")

    # Remove invalid data.
    scOpen('/tmp/sudoWork/sudo.ldif').replace('{0}sudo', 'sudo')

    # Remove last 8 (invalid) lines.
    scOpen('/tmp/sudoWork/sudo.ldif').remove_eof(8)

    # Load the schema into the LDAP server
    ldapadd("admin", open("/tmp/sudoWork/sudo.ldif").readlines())

    x("rm -rf /tmp/sudoWork")

    # Add index to sudoers db
    ldapadd("admin", """
dn: olcDatabase={2}bdb,cn=config
changetype: modify
add: olcDbIndex
olcDbIndex: sudoUser eq""")

def create_modules():
    '''
    Create the ldap node that are used to dynamically load overlay modules.

    '''
    ldapadd("admin", """
dn: cn=module{0},cn=config
objectClass: olcModuleList
cn: module{0}
olcModulePath: /usr/lib64/openldap/""")

def add_auditlog_overlay():
    '''
    Add auditlog overlay.

    Learn more:
        http://www.manpagez.com/man/5/slapo-auditlog/

    '''
    ldapadd("admin", """
dn: cn=module{0},cn=config
changetype:modify
add: olcModuleLoad
olcModuleLoad: auditlog.la

dn: olcOverlay=auditlog,olcDatabase={2}bdb,cn=config
changetype: add
objectClass: olcOverlayConfig
objectClass: olcAuditLogConfig
olcOverlay: auditlog
olcAuditlogFile: /var/log/slapd/auditlog.log
""")

def add_pwdpolicy_overlay():
    '''
    Add pwdpolicy overlay

    Learn more:
        http://www.zytrax.com/books/ldap/ch6/ppolicy.html
        http://www.openldap.org/software/man.cgi?query=slapo-ppolicy&sektion=5&apropos=0&manpath=OpenLDAP+2.3-Release
        http://www.symas.com/blog/?page_id=66
    '''
    ldapadd("admin", """
dn: cn=module{0},cn=config
changetype:modify
add: olcModuleLoad
olcModuleLoad: ppolicy.la

dn: olcOverlay=ppolicy,olcDatabase={2}bdb,cn=config
olcOverlay: ppolicy
objectClass: olcOverlayConfig
objectClass: olcPPolicyConfig
olcPPolicyHashCleartext: TRUE
olcPPolicyUseLockout: FALSE
olcPPolicyDefault: cn=default,ou=pwpolicies,%(ldap_dn)s
""" % {'ldap_dn': config.general.get_ldap_dn()})

def add_user_domain():
    '''
    Add users, groups, sudoers. To the dc=example,dc=com database.

    '''
    filenames = []

    # Add public domain.
    filenames.append(app.SYCO_PATH + "var/ldap/ldif/domain.ldif")

    # Add private domains.
    for dir in os.listdir(app.SYCO_USR_PATH):
        if dir =="mod-template":
            pass
        else:
            filenames.append(app.SYCO_USR_PATH + dir + "/var/ldap/ldif/domain.ldif")

    # Import the files
    for filename in filenames:
        filename = os.path.abspath(filename)
        if (os.access(filename, os.F_OK)):
            ldapadd("manager", open(filename).readlines())

def create_certs():
    '''
    Create all certificates that are needed by openldap.

    ca         - Signing client and server cert.
    slapd    - The server cert configured in the openldap server.
    client - All clients (sssd, ldapsearch etc.) need to send this with all their
                    requests.

    View cert info
    openssl x509 -text -in /etc/openldap/cacerts/ca.crt
    openssl x509 -text -in /etc/openldap/cacerts/slapd.crt
    openssl x509 -text -in /etc/openldap/cacerts/client.pem
    openssl req -noout -text -in /etc/openldap/cacerts/client.csr

    '''
    # Creating certs folder
    x("mkdir /etc/openldap/cacerts")

    create_ca_cert()
    create_server_cert()
    create_client_cert()
    set_permissions_on_certs()

def get_cert_subj(commonName):
    '''
    Return args for openssl "-subj" option.

    '''
    return "'/C=%s/ST=%s/L=%s/O=%s/OU=%s/CN=%s/emailAddress=%s'" % (
        config.general.get_country_name(),
        config.general.get_state(),
        config.general.get_locality(),
        config.general.get_organization_name(),
        config.general.get_organizational_unit_name(),
        commonName,
        config.general.get_admin_email()
    )

def create_ca_cert():
    x("echo '00' > /etc/openldap/cacerts/ca.srl")
    x("openssl req -new -x509 -sha512 -nodes -days 3650 -newkey rsa:4096" +
      " -out /etc/openldap/cacerts/ca.crt" +
      " -keyout /etc/openldap/cacerts/ca.key" +
      " -subj " + get_cert_subj(config.general.get_organization_name() + "CA"))

def create_server_cert():
    x("openssl req -new -sha512 -nodes -days 1095 -newkey rsa:4096 " +
      " -keyout /etc/openldap/cacerts/slapd.key" +
      " -out /etc/openldap/cacerts/slapd.csr" +
      " -subj " + get_cert_subj(config.general.get_ldap_hostname()))

    x("openssl x509 -req -sha512 -days 1095" +
      " -in /etc/openldap/cacerts/slapd.csr" +
      " -out /etc/openldap/cacerts/slapd.crt" +
      " -CA /etc/openldap/cacerts/ca.crt" +
      " -CAkey /etc/openldap/cacerts/ca.key")

def create_client_cert():
    # Create a CSR (Certificate Signing Request) file for client cert
    x("openssl req -new -sha512 -nodes -days 1095 -newkey rsa:4096" +
      " -keyout /etc/openldap/cacerts/client.key" +
      " -out /etc/openldap/cacerts/client.csr" +
      " -subj " + get_cert_subj(config.general.get_organization_name() + "client"))

    # Create a signed client crt.
    x("""cat > /etc/openldap/cacerts/sign.conf << EOF
[ v3_req ]
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature
subjectKeyIdentifier = hash
EOF""")

    x("openssl x509 -req -days 1095" +
      " -sha512" +
      " -extensions v3_req" +
      " -extfile /etc/openldap/cacerts/sign.conf" +
      " -CA /etc/openldap/cacerts/ca.crt" +
      " -CAkey /etc/openldap/cacerts/ca.key" +
      " -in /etc/openldap/cacerts/client.csr" +
      " -out /etc/openldap/cacerts/client.crt")

    # One file with both crt and key. Easier to manage the cert on client side.
    x("cat /etc/openldap/cacerts/client.crt" +
      " /etc/openldap/cacerts/client.key > " +
      " /etc/openldap/cacerts/client.pem")

def add_read_permission(filename):
    if (os.path.exists(filename)):
        x("chmod 744 " + filename)

def set_permissions_on_certs():
    # Create hash and set permissions of cert
    x("/usr/sbin/cacertdir_rehash /etc/openldap/cacerts")
    x("chown -Rf root:root /etc/openldap/cacerts")
    x("chmod -f 755 /etc/openldap/cacerts")
    x("restorecon -R /etc/openldap/cacerts")

    # root only access
    x("chmod -f 700 /etc/openldap/cacerts/*")
    add_read_permission("/etc/openldap/cacerts/ca.crt")
    add_read_permission("/etc/openldap/cacerts/client.pem")
    add_read_permission("/etc/openldap/cacerts/client.crt")
    add_read_permission("/etc/openldap/cacerts/client.key")
    add_read_permission("/etc/openldap/cacerts/slapd.crt")
    add_read_permission("/etc/openldap/cacerts/slapd.key")

def enable_ssl():
    '''
    Configure slapd to only be accessible over ssl,
    with client certificate.

    Learn more:
        http://www.openldap.org/pub/ksoper/OpenLDAP_TLS.html#4.0
        http://www.openldap.org/faq/data/cache/185.html

    '''
    ldapadd("admin", """
dn: cn=config
changetype:modify
replace: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/openldap/cacerts/slapd.key
-
replace: olcTLSCertificateFile
olcTLSCertificateFile: /etc/openldap/cacerts/slapd.crt
-
replace: olcTLSCACertificateFile
olcTLSCACertificateFile: /etc/openldap/cacerts/ca.crt
-
replace: olcTLSCipherSuite
olcTLSCipherSuite: HIGH:MEDIUM:-SSLv2
-
replace: olcTLSVerifyClient
olcTLSVerifyClient: allow""")

    # Enable LDAPS and dispable LDAP
    scOpen('/etc/sysconfig/ldap').replace('[#]*SLAPD_LDAPS=.*', 'SLAPD_LDAPS=yes')
    scOpen('/etc/sysconfig/ldap').replace('[#]*SLAPD_LDAP=.*', 'SLAPD_LDAP=no')
    x("service slapd restart")

    configure_client_cert_for_ldaptools()

def require_highest_security_from_clients():
    '''
    Required a high Security Strength Factor from clients.

    Learn more:
        http://www.openldap.org/doc/admin24/guide.html#Authentication Methods
    TODO:
        add olcSaslSecProps: noactive, nodict, passcred, minssf=128
        add olcSecurity: transport=128
        add olcSecurity: sasl=128
        add olcSecurity: update_ssl=128
        add olcSecurity: update_transport=128
        add olcSecurity: update_tls=128
        add olcSecurity: update_sasl=128

    '''
    ldapsadd("admin", """
dn: cn=config
changetype:modify
replace: olcLocalSSF
olcLocalSSF: 128
-
replace: olcSaslSecProps
olcSaslSecProps: noanonymous,noplain

dn: cn=config
changetype:modify
replace: olcSecurity
olcSecurity: ssf=128
olcSecurity: simple_bind=128
olcSecurity: tls=128""")


def get_hashed_password(password):
    '''
    Returns a seeded SHA-1 hashed password.

    get_hashed_password is used to generate an userPassword value suitable for
    use with ldapmodify(1), slapd.conf(5) rootpw configuration directive or the
    slapd-config(5) olcRootPW configura-tion directive.

    password
        The password that should be hashed.

    return
        ie. {SSHA}sR7O1GhqEUMiy14uliQdHo7pE0dwlmxL

    '''
    return x("slappasswd -h '{SSHA}' -s '" + password +"'").strip()

def ldapadd(user, value, uri="-H ldap:///"):
    '''
    Add ldif to openldap over ldap with shell command ldapadd.

    user
        The user used to bind with openldap.
        Only user 'admin' and 'manager' are allowed.

    value
        The ldif value that should be added to openldap.

    '''
    if user == 'admin':
        user = 'cn=config'
    elif user == 'manager':
        user = 'cn=Manager,' + config.general.get_ldap_dn()
    else:
        raise Exception("Only admin and manager users are supported by ldapXadd")

    if isinstance(value, ListType):
        tmpvalue = ""
        for val in value:
            tmpvalue += val
        value = tmpvalue

    x("ldapadd %s -x -D '%s' -w '%s' << EOF\n%s\nEOF\n\n" % (
        uri,
        user,
        app.get_ldap_admin_password(),
        value
    ))

def ldapsadd(user, value):
    '''
    Add ldif to openldap over ldaps with shell command ldapadd.

    '''
    ldapadd(user, value, '')

def setup_hosts():
    '''
    Communication with the LDAP-server needs to be done with domain name, and not
    the ip. This ensures the dns-name is configured.

    '''
    scOpen('/etc/hosts').remove('^' + config.general.get_ldap_server_ip() + '.*')
    scOpen('/etc/hosts').add(
        '%(ldap_ip)s %(domain_name)s' % {
            'ldap_ip' : config.general.get_ldap_server_ip(),
            'domain_name' : config.general.get_ldap_hostname()
        }
    )

def configure_client_cert_for_ldaptools():
    '''
    Configure the client cert to be used by ldaptools (ldapsearch etc.).

    This is done by setting environment variables for all users in /etc/profile

    '''
    scOpen("/etc/profile").remove(
        "^LDAPTLS_CERT.*\|^LDAPTLS_KEY.*\|export LDAPTLS_CERT LDAPTLS_KEY.*"
    )
    scOpen("/etc/profile").add(
        "LDAPTLS_CERT=/etc/openldap/cacerts/client.pem\n" +
        "LDAPTLS_KEY=/etc/openldap/cacerts/client.pem\n" +
        "export LDAPTLS_CERT LDAPTLS_KEY"
    )

###########################################################
# Debug/Testing
#
# Need to install client before ldapsearch will work.
###########################################################

# Test config files
# slaptest -u

# Enable Debug logging
# ldapadd -x -D 'cn=config' -w '<password>' << EOF
# dn: cn=config
# changetype:modify
# replace: olcLogLevel
# olcLogLevel: config stats shell
# EOF


# Verify the client-cert auth
# openssl s_client -connect localhost:636 -state \
#         -CAfile /etc/openldap/cacerts/ca.crt \
#         -cert /etc/openldap/cacerts/client.pem \
#         -key /etc/openldap/cacerts/client.pem
# ldapsearch -x -D "cn=config" -w secret    -v -d1

# List all info from the dc=syco,dc=net database.
# ldapsearch -D "cn=Manager,dc=syco,dc=net" -w secret -b dc=syco,dc=net -e ppolicy

# List the sudo.schema
# ldapsearch -D "cn=config" -w secret -b cn={12}sudo,cn=schema,cn=config

# Verify that the AuditLog is configured.
# ldapsearch -D "cn=config" -w secret -b olcDatabase={2}bdb,cn=config

# List root DN:s, controls, featurs etc.
# ldapsearch -LLL -x    -b "" -s base +

#
# ldapsearch -D "cn=config" -w secret -x -b "dc=syco,dc=net" -e ppolicy objectclass=posixAccount

# List all relevant database options.
# ldapsearch -D "cn=config" -w secret -b cn=config
# ldapsearch -D "cn=config" -w secret -b cn=config cn=config
# ldapsearch -D "cn=config" -w secret -b cn=config schema
# ldapsearch -D "cn=config" -w secret -b cn=schema,cn=config
# ldapsearch -D "cn=config" -w secret -b cn=config olcDatabase={0}config
# ldapsearch -D "cn=config" -w secret -b cn=config olcDatabase={-1}frontend
# ldapsearch -D "cn=config" -w secret -b cn=config olcDatabase={2}bdb
# ldapsearch -D "cn=config" -w secret -b cn=config olcDatabase={2}monitor
# ldapsearch -D "cn=config" -w secret -b cn=config 'cn=module*'
# ldapsearch -D "cn=Manager,dc=syco,dc=net" -w secret    olcDatabase={2}monitor,cn=config


# ldapsearch -D "cn=config" -w secret -b cn=config 'cn=module*'
# ldapsearch -D "cn=config" -w secret -b dc=syco,dc=net cn=default
# ldapsearch -D "cn=config" -w secret -b olcDatabase={}bdb,cn=config olcOverlay=ppolicy
# ldapsearch -D "cn=config" -w secret -b uid=user4,ou=people,dc=syco,dc=net
# # Return my self.
# ldapsearch -b uid=user1,ou=people,dc=syco,dc=net -D "uid=user1,ou=people,dc=syco,dc=net" -w fratsecret

# Unlock ppolicy locked account
# ldapadd -D "cn=config" -W
# dn: uid=danlin,ou=people,dc=fareoffice,dc=com
# changetype: modify
# delete: pwdAccountLockedTime
#
# Unlock ppolicy locked account or remove the pwdMinAge
# dn: uid=danlin,ou=people,dc=fareoffice,dc=com
# changetype: modify
# add: pwdReset
# pwdReset: TRUE

###########################################################
# Add accesslog overlay.
#
# http://www.manpagez.com/man/5/slapo-accesslog/
#
# TODO: Didn't get it working.
#
###########################################################
# ldapadd -H ldap:/// -x -D "cn=config" -w secret << EOF
# dn: cn=module,cn=config
# objectClass: olcModuleList
# cn: module
# olcModulePath: /usr/lib64/openldap/
# olcModuleLoad: access.la
#
#
# dn: olcOverlay=accesslog,olcDatabase={1}bdb,cn=config
# changetype: add
# olcOverlay: accesslog
# objectClass: olcOverlayConfig
# objectClass: olcAccessLogConfig
# logdb: cn=auditlog
# logops: writes reads
# # read log every 5 days and purge entries
# # when older than 30 days
# logpurge 180+00:00 5+00:00
# # optional - saves the previous contents of
# # person objectclass before performing a write operation
# logold: (objectclass=person)
# EOF
