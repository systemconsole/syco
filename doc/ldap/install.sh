#!/bin/sh
#
# This script is based on information from at least the following links.
#   https://help.ubuntu.com/10.04/serverguide/C/openldap-server.html
#   http://home.roadrunner.com/~computertaijutsu/ldap.html
#   http://www.salsaunited.net/blog/?p=74
#   http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=3
#   http://www.server-world.info/en/note?os=CentOS_6&p=ldap

###########################################################
# Uninstall LDAP-server
#
# Remove old LDAP-server installation.
# This is only used for debug purpose when testing different
# options.
#
###########################################################

service slapd stop
rm -rf /etc/openldap/slapd.d/
rm -rf /var/lib/ldap/*
yum -y remove openldap-servers

rm -f /var/log/audit/audit.log
service auditd restart

###########################################################
# Install LDAP-server
#
# This part should only be executed on the LDAP-Server
###########################################################

# Enable SELinux for higher security.
setenforce 1
setsebool -P domain_kernel_load_modules 1

# Communication with the LDAP-server needs to be done with domain name, and not
# the ip. This ensures the dns-name is configured.
sed -i '/127.0.0.1/s/ ldap.syco.net//' /etc/hosts
sed -i '/127.0.0.1/s/$/ ldap.syco.net/' /etc/hosts

# Install packages
yum -y install openldap-servers openldap-clients

# Setup iptables
iptables -I INPUT -m state --state NEW -p tcp --dport 636 -j ACCEPT
iptables -I OUTPUT -m state --state NEW -p tcp --dport 636 -j ACCEPT

#
# Setup certificates
#

# Create CA
echo "00" > /etc/openldap/cacerts/ca.srl
openssl req -new -x509 -sha256 -nodes -days 3650 -newkey rsa:4096\
    -out /etc/openldap/cacerts/ca.crt \
    -keyout /etc/openldap/cacerts/ca.key \
    -subj '/O=syco/OU=System Console Project/CN=systemconsole.github.com'

# Creating server cert
openssl req -new -sha256 -nodes -days 1095 -newkey rsa:4096 \
    -keyout /etc/openldap/cacerts/slapd.key \
    -out /etc/openldap/cacerts/slapd.csr \
    -subj '/O=syco/OU=System Console Project/CN=ldap.syco.net'
openssl x509 -req -sha256 -days 1095 \
    -in /etc/openldap/cacerts/slapd.csr \
    -out /etc/openldap/cacerts/slapd.crt \
    -CA /etc/openldap/cacerts/ca.crt \
    -CAkey /etc/openldap/cacerts/ca.key

/usr/sbin/cacertdir_rehash /etc/openldap/cacerts
chown -Rf root:ldap /etc/openldap/cacerts
chmod -Rf 750 /etc/openldap/cacerts
restorecon -R /etc/openldap/cacerts

# View cert info
# openssl x509 -text -in ca.crt
# openssl x509 -text -in slapd.crt

#
# Configure LDAP-server
#

# Create backend database.
cp /usr/share/doc/openldap-servers-2.4.19/DB_CONFIG.example /var/lib/ldap/DB_CONFIG
chown -R ldap:ldap /var/lib/ldap

# Set password for cn=admin,cn=config (it's secret)
cat >> /etc/openldap/slapd.d/cn\=config/olcDatabase\=\{0\}config.ldif << EOF
olcRootPW: {SSHA}OjXYLr1oZ/LrHHTmjnPWYi1GjbgcYxSb
EOF

# Test config files
slaptest -u

# Start ldap server
service slapd start
chkconfig slapd on

# Wait for slapd to start.
sleep 1

# Create a password that can be inserted into the ldif files.
# echo `slappasswd -s secret`

# General configuration of the server.
ldapadd -H ldap:/// -x -D "cn=admin,cn=config" -w secret -f general.ldif

# Setup the dc=syco,dc=net databas.
ldapadd -H ldap:/// -x -D "cn=Manager,dc=syco,dc=net" -w secret  -f manager.ldif

# Enable LDAPS and dispable LDAP
sed -i 's/[#]*SLAPD_LDAPS=.*/SLAPD_LDAPS=yes/g' /etc/sysconfig/ldap
sed -i 's/[#]*SLAPD_LDAP=.*/SLAPD_LDAP=no/g' /etc/sysconfig/ldap
service slapd restart

# List all info from the dc=syco,dc=net database.
# ldapsearch -H ldaps://ldap.syco.net -x -D "cn=Manager,dc=syco,dc=net" -w secret -xLLL -b dc=syco,dc=net

# List all relevant database options.
# ldapsearch -H ldaps://ldap.syco.net -x -D "cn=admin,cn=config" -w secret -xLLL -b cn=config cn=config
# ldapsearch -H ldaps://ldap.syco.net -x -D "cn=admin,cn=config" -w secret -xLLL -b cn=config schema
# ldapsearch -H ldaps://ldap.syco.net -x -D "cn=admin,cn=config" -w secret -xLLL -b cn=config olcDatabase={0}config
# ldapsearch -H ldaps://ldap.syco.net -x -D "cn=admin,cn=config" -w secret -xLLL -b cn=config olcDatabase={-1}frontend
# ldapsearch -H ldaps://ldap.syco.net -x -D "cn=admin,cn=config" -w secret -xLLL -b cn=config olcDatabase={1}bdb
# ldapsearch -H ldaps://ldap.syco.net -x -D "cn=admin,cn=config" -w secret -xLLL -b cn=config olcDatabase={2}monitor

# List all database options.
# ldapsearch -H ldaps://ldap.syco.net -x -D "cn=admin,cn=config" -w secret -xLLL -b cn=config

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

# Install packages
yum -y install openldap-clients sssd

# Communication with the LDAP-server needs to be done with domain name, and not
# the ip. This ensures the dns-name is configured.
sed -i '/127.0.0.1/s/ ldap.syco.net//' /etc/hosts
sed -i '/127.0.0.1/s/$/ ldap.syco.net/' /etc/hosts

# Get certificate from ldap server
scp root@10.100.110.7:/etc/openldap/cacerts/slapd.crt /etc/openldap/cacerts/slapd.crt

/usr/sbin/cacertdir_rehash /etc/openldap/cacerts
chown -Rf root:ldap /etc/openldap/cacerts
chmod -Rf 750 /etc/openldap/cacerts
restorecon -R /etc/openldap/cacerts

# Setup iptables
iptables -I OUTPUT -m state --state NEW -p tcp --dport 636 -j ACCEPT

# Configure all relevant /etc files for ssd, ldap etc.
authconfig \
    --enablesssd --enablesssdauth --enablecachecreds \
    --enableldap --enableldaptls --enableldapauth \
    --ldapserver=ldaps://ldap.syco.net --ldapbasedn=dc=syco,dc=net \
    --disablenis \
    --enableshadow --enablemkhomedir --enablelocauthorize \
    --passalgo=sha512 \
    --updateall

#
# Configure sssd
#

# If the authentication provider is offline, specifies for how long to allow
# cached log-ins (in days). This value is measured from the last successful
# online log-in. If not specified, defaults to 0 (no limit).
sed -i '/\[pam\]/a offline_credentials_expiration=5' /etc/sssd/sssd.conf

# Enumeration means that the entire set of available users and groups on the
# remote source is cached on the local machine. When enumeration is disabled,
# users and groups are only cached as they are requested.
sed -i '/\[domain\/default\]/a enumerate=true' /etc/sssd/sssd.conf

# Restart sssd
chkconfig sssd on
service sssd restart

# Test connection to ldap server
ldapsearch -xLLL -b dc=syco,dc=net -D "cn=Manager,dc=syco,dc=net" -w secret
ldapsearch -xLLL -b dc=syco,dc=net -D "uid=user4,ou=people,dc=syco,dc=net" -w fratsecret

# Test sssd
getent passwd
getent group

# Use this?
#   authconfig --ldaploadcacert=<URL>   load CA certificate from the URL
#   nss_base_hosts         ou=Hosts,dc=example,dc=com?one
