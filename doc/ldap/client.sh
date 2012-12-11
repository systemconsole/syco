#!/bin/sh
#
###########################################################
# Install LDAP-client
#
# This part should be executed on both LDAP-Server and
# on all clients that should authenticate against the
# LDAP-server
#
# This script is based on information from at least the following links.
#   http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=2
#   http://docs.fedoraproject.org/en-US/Fedora/15/html/Deployment_Guide/chap-SSSD_User_Guide-Introduction.html
#   http://directory.fedoraproject.org/wiki/Howto:PAM
#
###########################################################

###########################################################
# Uninstall sssd
#
# Note: Only needed if sssd has been setup before.
#       might need --skip-broken when installing sssd.
###########################################################
#yum -y remove openldap-clients sssd
#rm -rf /var/lib/sss/

###########################################################
# Install relevant packages
###########################################################
# Install packages
yum -y install openldap-clients authconfig

# Pick one package from the Continuous Release
# Version 1.5.1 of sssd.
yum -y install sssd --skip-broken
yum -y install centos-release-cr
yum -y update sssd
yum -y remove centos-release-cr

###########################################################
# Get certificate from ldap server
#
# This is not needed to be done on the server.
###########################################################
if [ ! -f /etc/openldap/cacerts/client.pem ];
then
    scp root@10.100.110.7:/etc/openldap/cacerts/client.pem /etc/openldap/cacerts/client.pem
fi

if [ ! -f /etc/openldap/cacerts/ca.crt ];
then
    scp root@10.100.110.7:/etc/openldap/cacerts/ca.crt /etc/openldap/cacerts/ca.crt
fi

/usr/sbin/cacertdir_rehash /etc/openldap/cacerts
chown -Rf root:ldap /etc/openldap/cacerts
chmod -Rf 750 /etc/openldap/cacerts
restorecon -R /etc/openldap/cacerts

###########################################################
# Configure client authenticate against ldap.
###########################################################
# Setup iptables before configuring sssd, so it can connect to the server.
iptables -I OUTPUT -m state --state NEW -p tcp -d 10.100.110.7 --dport 636 -j ACCEPT

# Communication with the LDAP-server needs to be done with domain name, and not
# the ip. This ensures the dns-name is configured.
sed -i '/^10.100.110.7.*/d' /etc/hosts
cat >> /etc/hosts << EOF
10.100.110.7 ldap.syco.net
EOF

# Configure all relevant /etc files for sssd, ldap etc.
authconfig \
    --enablesssd --enablesssdauth --enablecachecreds \
    --enableldap --enableldaptls --enableldapauth \
    --ldapserver=ldaps://ldap.fareoffice.com --ldapbasedn=dc=fareoffice,dc=com \
    --disablenis --disablekrb5 \
    --enableshadow --enablemkhomedir --enablelocauthorize \
    --passalgo=sha512 \
    --updateall

# Configure the client cert to be used by ldapsearch for user root.
sed -i '/^TLS_CERT.*\|^TLS_KEY.*/d' /root/ldaprc
cat >> /root/ldaprc  << EOF
TLS_CERT /etc/openldap/cacerts/client.pem
TLS_KEY /etc/openldap/cacerts/client.pem
EOF

###########################################################
# Configure sssd
###########################################################

# If the authentication provider is offline, specifies for how long to allow
# cached log-ins (in days). This value is measured from the last successful
# online log-in. If not specified, defaults to 0 (no limit).
sed -i '/\[pam\]/a offline_credentials_expiration=5' /etc/sssd/sssd.conf

cat >> /etc/sssd/sssd.conf << EOF
# Enumeration means that the entire set of available users and groups on the
# remote source is cached on the local machine. When enumeration is disabled,
# users and groups are only cached as they are requested.
enumerate=true

# Configure client certificate auth.
ldap_tls_cert = /etc/openldap/cacerts/client.pem
ldap_tls_key = /etc/openldap/cacerts/client.pem
ldap_tls_reqcert = demand

# Only users with this employeeType are allowed to login to this computer.
access_provider = ldap
ldap_access_filter = (employeeType=Sysop)

# Login to ldap with a specified user.
ldap_default_bind_dn = cn=sssd,dc=fareoffice,dc=com
ldap_default_authtok_type = password
ldap_default_authtok = secret
EOF

# Restart sssd
service sssd restart

# Start sssd after reboot.
chkconfig sssd on

###########################################################
# Configure the client to use sudo
###########################################################
sed -i '/^sudoers.*/d' /etc/nsswitch.conf
cat >> /etc/nsswitch.conf << EOF
sudoers: ldap files
EOF

sed -i '/^sudoers_base.*\|^binddn.*\|^bindpw.*\|^ssl on.*\|^tls_cert.*\|^tls_key.*\|sudoers_debug.*/d' /etc/ldap.conf
cat >> /etc/ldap.conf << EOF
# Configure sudo ldap.
uri ldaps://ldap.syco.net
base dc=fareoffice,dc=com
sudoers_base ou=SUDOers,dc=fareoffice,dc=com
binddn cn=sssd,dc=fareoffice,dc=com
bindpw secret
ssl on
tls_cacertdir /etc/openldap/cacerts
tls_cert /etc/openldap/cacerts/client.pem
tls_key /etc/openldap/cacerts/client.pem
#sudoers_debug 5
EOF

###########################################################
# Test to see that everything works fine.
###########################################################

# Should return everything.
# ldapsearch -b dc=fareoffice,dc=com -D "cn=Manager,dc=fareoffice,dc=com" -w secret

# Return my self.
# ldapsearch -b uid=user1,ou=people,dc=fareoffice,dc=com -D "uid=user1,ou=people,dc=fareoffice,dc=com" -w fratsecret

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
