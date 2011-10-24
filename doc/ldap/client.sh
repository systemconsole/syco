#!/bin/sh
#
###########################################################
# Install LDAP-client
#
# This part should be executed on both LDAP-Server and
# on all clients that should authenticate against the
# LDAP-server
#
###########################################################

# Client installation
#
# This script is based on information from at least the following links.
#   http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=2
#   http://docs.fedoraproject.org/en-US/Fedora/15/html/Deployment_Guide/chap-SSSD_User_Guide-Introduction.html
#

# Uninstall sssd
# Note: Only needed if sssd has been setup before.
#TODO yum -y remove openldap-clients sssd
#TODO rm -rf /var/lib/sss/


# Install packages
#TODO yum -y install openldap-clients sssd

# Pick one package from the Continuous Release
# Version 1.5.1 of sssd.
#TODO yum -y install centos-release-cr
#TODO yum -y update sssd
#TODO yum -y remove centos-release-cr

# Communication with the LDAP-server needs to be done with domain name, and not
# the ip. This ensures the dns-name is configured.
sed -i '/^10.100.110.7.*/d' /etc/hosts
cat >> /etc/hosts << EOF
10.100.110.7 ldap.syco.net
EOF

# Get certificate from ldap server
#TODO scp root@10.100.110.7:/etc/openldap/cacerts/client.pem /etc/openldap/cacerts/client.pem
#TODO scp root@10.100.110.7:/etc/openldap/cacerts/ca.crt /etc/openldap/cacerts/ca.crt

/usr/sbin/cacertdir_rehash /etc/openldap/cacerts
chown -Rf root:ldap /etc/openldap/cacerts
chmod -Rf 750 /etc/openldap/cacerts
restorecon -R /etc/openldap/cacerts

# Setup iptables
iptables -I OUTPUT -m state --state NEW -p tcp -d 10.100.110.7 --dport 636 -j ACCEPT

# Configure all relevant /etc files for ssd, ldap etc.
authconfig \
    --enablesssd --enablesssdauth --enablecachecreds \
    --enableldap --enableldaptls --enableldapauth \
    --ldapserver=ldaps://ldap.syco.net --ldapbasedn=dc=syco,dc=net \
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

#
# Configure sssd
#

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
ldap_default_bind_dn = cn=sssd,dc=syco,dc=net
ldap_default_authtok_type = password
ldap_default_authtok = secret
EOF

# Restart sssd
service sssd restart

# Start sssd after reboot.
chkconfig sssd on


# Configure the client to use sudo
cat >> /etc/nsswitch.conf << EOF
sudoers: ldap files
EOF

cat >> /etc/openldap/ldap.conf << EOF

# Configure sudo ldap.
sudoers_base ou=SUDOers,dc=syco,dc=net
binddn cn=sssd,dc=syco,dc=net
bindpw secret
ssl on
tls_cert /etc/openldap/cacerts/client.pem
tls_key /etc/openldap/cacerts/client.pem
#sudoers_debug 5
EOF

# Looks like sudo reads directly from /etc/ldap.conf
ln /etc/openldap/ldap.conf /etc/ldap.conf

#
# Test to see that everything works fine.
#

# Should return everything.
#ldapsearch -b dc=syco,dc=net -D "cn=Manager,dc=syco,dc=net" -w secret

# Return my self.
#ldapsearch -b uid=user4,ou=people,dc=syco,dc=net -D "uid=user4,ou=people,dc=syco,dc=net" -w fratsecret

# Can't access somebody else
#ldapsearch -b uid=user3,ou=people,dc=syco,dc=net -D "uid=user4,ou=people,dc=syco,dc=net" -w fratsecret

# Should return nothing.
#ldapsearch -b dc=syco,dc=net -D ""

# Test sssd
#getent passwd
#getent group

# Test if sudo is using LDAP.
#sudo -l