#!/bin/sh
#
# This script is based on information from at least the following links.
#   http://www.openldap.org/doc/admin24/guide.html
#   https://help.ubuntu.com/10.04/serverguide/C/openldap-server.html
#   http://home.roadrunner.com/~computertaijutsu/ldap.html
#   http://www.salsaunited.net/blog/?p=74
#   http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=3
#   http://www.server-world.info/en/note?os=CentOS_6&p=ldap
#   http://linux.die.net/man/5/slapd-config
#   http://eatingsecurity.blogspot.com/2008/11/openldap-security.html
#   http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/ch-Directory_Servers.html#s1-OpenLDAP
#   http://www.howtoforge.com/linux_ldap_authentication
#
# * Create a password that can be inserted into the ldif files.
#   echo `slappasswd -s secret`
#

###########################################################
# Uninstall LDAP-server
#
# Remove old LDAP-server installation.
# This is only used for debug purpose when testing different
# options.
#
###########################################################
service slapd stop
yum -y remove openldap-servers
rm -rf /etc/openldap/slapd.d/
rm -rf /var/lib/ldap/*

# Remove client cert configs
sed -i '/^TLS_CERT.*\|^TLS_KEY.*/d' /root/ldaprc

# Remove sudo configs.
sed -i '/# Configure sudo ldap/d' /etc/openldap/ldap.conf
sed -i '/^sudoers.*/d' /etc/nsswitch.conf
sed -i '/^sudoers_base.*\|^binddn.*\|^bindpw.*\|^ssl on.*\|^tls_cert.*\|^tls_key.*\|sudoers_debug.*/d' /etc/ldap.conf

# Host information
sed -i '/^10.100.110.7.*/d' /etc/hosts

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
cat >> /etc/hosts << EOF
10.100.110.7 ldap.syco.net
EOF

# Install all required packages.
yum -y install openldap-servers openldap-clients

# Create backend database.
cp /usr/share/doc/openldap-servers-2.4.19/DB_CONFIG.example /var/lib/ldap/DB_CONFIG
chown -R ldap:ldap /var/lib/ldap

# Set password for cn=admin,cn=config (it's secret)
cat >> /etc/openldap/slapd.d/cn\=config/olcDatabase\=\{0\}config.ldif << EOF
olcRootPW: {SSHA}OjXYLr1oZ/LrHHTmjnPWYi1GjbgcYxSb
EOF

# Autostart slapd after reboot.
chkconfig slapd on

# Start ldap server
service slapd start

# Wait for slapd to start.
sleep 1

###########################################################
# General configuration of the server.
###########################################################

# Create folder to store log files in
mkdir /var/log/slapd
chmod 755 /var/log/slapd/
chown ldap:ldap /var/log/slapd/

# Redirect all log files through rsyslog.
sed -i "/local4.*/d" /etc/rsyslog.conf
cat >> /etc/rsyslog.conf << EOF
local4.*                        /var/log/slapd/slapd.log
EOF
service rsyslog restart

# Do the configurations.
ldapadd -H ldap://ldap.syco.net -x -D "cn=admin,cn=config" -w secret << EOF

# Setup logfile (not working now, propably needing debug level settings.)
dn: cn=config
changetype:modify
replace: olcLogLevel
olcLogLevel: config stats shell
-
replace: olcIdleTimeout
olcIdleTimeout: 30

# Set access for the monitor db.
dn: olcDatabase={2}monitor,cn=config
changetype: modify
replace: olcAccess
olcAccess: {0}to * by dn.base="cn=Manager,dc=syco,dc=net" read  by * none

# Set password for cn=admin,cn=config
dn: olcDatabase={0}config,cn=config
changetype: modify
replace: olcRootPW
olcRootPW: {SSHA}OjXYLr1oZ/LrHHTmjnPWYi1GjbgcYxSb

# Change LDAP-domain, password and access rights.
dn: olcDatabase={1}bdb,cn=config
changetype: modify
replace: olcSuffix
olcSuffix: dc=syco,dc=net
-
replace: olcRootDN
olcRootDN: cn=Manager,dc=syco,dc=net
-
replace: olcRootPW
olcRootPW: {SSHA}OjXYLr1oZ/LrHHTmjnPWYi1GjbgcYxSb
-
replace: olcAccess
olcAccess: {0}to attrs=employeeType by dn="cn=sssd,dc=syco,dc=net" read by self read by * none
olcAccess: {1}to attrs=userPassword,shadowLastChange by self write by anonymous auth by * none
olcAccess: {2}to dn.base="" by * none
olcAccess: {3}to * by dn="cn=admin,cn=config" write by dn="cn=sssd,dc=syco,dc=net" read by self write by * none
EOF

##########################################################
# Configure sudo in ldap
#
# Users that should have sudo rights, are configured in
# in the ldap-db. The ldap sudo schema are not configured
# by default, and are here created.
#
# http://eatingsecurity.blogspot.com/2008/10/openldap-continued.html
# http://www.sudo.ws/sudo/man/1.8.2/sudoers.ldap.man.html
##########################################################

# Copy the sudo Schema into the LDAP schema repository
/bin/cp -f /usr/share/doc/sudo-1.7.2p2/schema.OpenLDAP /etc/openldap/schema/sudo.schema
restorecon /etc/openldap/schema/sudo.schema

# Create a conversion file for schema
mkdir ~/sudoWork
echo "include /etc/openldap/schema/sudo.schema" > ~/sudoWork/sudoSchema.conf

# Convert the "Schema" to "LDIF".
slapcat -f ~/sudoWork/sudoSchema.conf -F /tmp/ -n0 -s "cn={0}sudo,cn=schema,cn=config" > ~/sudoWork/sudo.ldif

# Remove invalid data.
sed -i "s/{0}sudo/sudo/g" ~/sudoWork/sudo.ldif

# Remove last 8 (invalid) lines.
head -n-8 ~/sudoWork/sudo.ldif > ~/sudoWork/sudo2.ldif

# Load the schema into the LDAP server
ldapadd -H ldap:/// -x -D "cn=admin,cn=config" -w secret -f ~/sudoWork/sudo2.ldif

# Add index to sudoers db
ldapadd -H ldap:/// -x -D "cn=admin,cn=config" -w secret << EOF
dn: olcDatabase={1}bdb,cn=config
changetype: modify
add: olcDbIndex
olcDbIndex: sudoUser    eq
EOF

###########################################################
# Create modules area
#
###########################################################
ldapadd -H ldap:/// -x -D "cn=admin,cn=config" -w secret << EOF
dn: cn=module{0},cn=config
objectClass: olcModuleList
cn: module{0}
olcModulePath: /usr/lib64/openldap/
EOF

###########################################################
# Add auditlog overlay.
#
# http://www.manpagez.com/man/5/slapo-auditlog/
###########################################################
ldapadd -H ldap:/// -x -D "cn=admin,cn=config" -w secret << EOF
dn: cn=module{0},cn=config
changetype:modify
add: olcModuleLoad
olcModuleLoad: auditlog.la

dn: olcOverlay=auditlog,olcDatabase={1}bdb,cn=config
changetype: add
objectClass: olcOverlayConfig
objectClass: olcAuditLogConfig
olcOverlay: auditlog
olcAuditlogFile: /var/log/slapd/auditlog.log
EOF

###########################################################
# Add accesslog overlay.
#
# http://www.manpagez.com/man/5/slapo-accesslog/
#
# TODO: Didn't get it working.
#
###########################################################
# ldapadd -H ldap:/// -x -D "cn=admin,cn=config" -w secret << EOF
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

###########################################################
# Add pwdpolicy overlay
#
# http://www.zytrax.com/books/ldap/ch6/ppolicy.html
# http://www.openldap.org/software/man.cgi?query=slapo-ppolicy&sektion=5&apropos=0&manpath=OpenLDAP+2.3-Release
# http://www.symas.com/blog/?page_id=66
###########################################################

ldapadd -H ldap:/// -x -D "cn=admin,cn=config" -w secret << EOF
dn: cn=module{0},cn=config
changetype:modify
add: olcModuleLoad
olcModuleLoad: ppolicy.la

dn: olcOverlay=ppolicy,olcDatabase={1}bdb,cn=config
olcOverlay: ppolicy
objectClass: olcOverlayConfig
objectClass: olcPPolicyConfig
olcPPolicyHashCleartext: TRUE
olcPPolicyUseLockout: FALSE
olcPPolicyDefault: cn=default,ou=pwpolicies,dc=syco,dc=net
EOF

##########################################################
# Add users, groups, sudoers. Ie. the dc=syco,dc=net database.
##########################################################
ldapadd  -H ldap:/// -x -D "cn=Manager,dc=syco,dc=net" -w secret  -f /opt/syco/doc/ldap/manager.ldif

###########################################################
# Create certificates
###########################################################

# Create CA
echo "00" > /etc/openldap/cacerts/ca.srl
openssl req -new -x509 -sha512 -nodes -days 3650 -newkey rsa:4096\
    -out /etc/openldap/cacerts/ca.crt \
    -keyout /etc/openldap/cacerts/ca.key \
    -subj '/O=syco/OU=System Console Project/CN=systemconsole.github.com'

# Creating server cert
openssl req -new -sha512 -nodes -days 1095 -newkey rsa:4096 \
    -keyout /etc/openldap/cacerts/slapd.key \
    -out /etc/openldap/cacerts/slapd.csr \
    -subj '/O=syco/OU=System Console Project/CN=ldap.syco.net'
openssl x509 -req -sha512 -days 1095 \
    -in /etc/openldap/cacerts/slapd.csr \
    -out /etc/openldap/cacerts/slapd.crt \
    -CA /etc/openldap/cacerts/ca.crt \
    -CAkey /etc/openldap/cacerts/ca.key

#
# Customer create a CSR (Certificate Signing Request) file for client cert
#
openssl req -new -sha512 -nodes -days 1095 -newkey rsa:4096 \
    -keyout /etc/openldap/cacerts/client.key \
    -out /etc/openldap/cacerts/client.csr \
    -subj '/O=syco/OU=System Console Project/CN=client.syco.net'

#
# Create a signed client crt.
#
cat > /etc/openldap/cacerts/sign.conf << EOF
[ v3_req ]
basicConstraints = critical,CA:FALSE
keyUsage = critical,digitalSignature
subjectKeyIdentifier = hash
EOF

openssl x509 -req -days 1095 \
    -sha512 \
    -extensions v3_req \
    -extfile /etc/openldap/cacerts/sign.conf \
    -CA /etc/openldap/cacerts/ca.crt \
    -CAkey /etc/openldap/cacerts/ca.key \
    -in /etc/openldap/cacerts/client.csr \
    -out /etc/openldap/cacerts/client.crt

# One file with both crt and key. Easier to manage the cert on client side.
cat /etc/openldap/cacerts/client.crt /etc/openldap/cacerts/client.key > \
    /etc/openldap/cacerts/client.pem

# Create hash and set permissions of cert
/usr/sbin/cacertdir_rehash /etc/openldap/cacerts
chown -Rf root:ldap /etc/openldap/cacerts
chmod -Rf 750 /etc/openldap/cacerts
restorecon -R /etc/openldap/cacerts

# View cert info
# openssl x509 -text -in /etc/openldap/cacerts/ca.crt
# openssl x509 -text -in /etc/openldap/cacerts/slapd.crt
# openssl x509 -text -in /etc/openldap/cacerts/client.pem
# openssl req -noout -text -in /etc/openldap/cacerts/client.csr

###########################################################
# Configure ssl
#
# Configure slapd to only be accessible over ssl,
# with client certificate.
#
# http://www.openldap.org/pub/ksoper/OpenLDAP_TLS.html#4.0
# http://www.openldap.org/faq/data/cache/185.html
###########################################################
ldapadd -H ldap:/// -x -D "cn=admin,cn=config" -w secret << EOF
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
olcTLSVerifyClient: demand
EOF

# Enable LDAPS and dispable LDAP
sed -i 's/[#]*SLAPD_LDAPS=.*/SLAPD_LDAPS=yes/g' /etc/sysconfig/ldap
sed -i 's/[#]*SLAPD_LDAP=.*/SLAPD_LDAP=no/g' /etc/sysconfig/ldap
service slapd restart

# Configure the client cert to be used by ldapsearch for user root.
sed -i '/^TLS_CERT.*\|^TLS_KEY.*/d' /root/ldaprc
cat >> /root/ldaprc  << EOF
TLS_CERT /etc/openldap/cacerts/client.pem
TLS_KEY /etc/openldap/cacerts/client.pem
EOF

###########################################################
# Require higher security from clients.
###########################################################
ldapadd -H ldaps://ldap.syco.net -x -D "cn=admin,cn=config" -w secret << EOF
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
olcSecurity: tls=128
EOF

###########################################################
# Open firewall
#
# Let clients connect to the server through the firewall.
# This is done after everything else is done, so we are sure
# that the server is secure before letting somebody in.
# TODO: Add destination ip
###########################################################
iptables -I INPUT -m state --state NEW -p tcp -s 10.100.110.7/24 --dport 636 -j ACCEPT

###########################################################
# Debug/Testing
#
# Need to install client before ldapsearch will work.
###########################################################

# Test config files
# slaptest -u

# Verify the client-cert auth
# openssl s_client -connect localhost:636 -state \
#     -CAfile /etc/openldap/cacerts/ca.crt \
#     -cert /etc/openldap/cacerts/client.pem \
#     -key /etc/openldap/cacerts/client.pem
# ldapsearch -x -D "cn=admin,cn=config" -w secret  -v -d1

# List all info from the dc=syco,dc=net database.
# ldapsearch -D "cn=Manager,dc=syco,dc=net" -w secret -b dc=syco,dc=net -e ppolicy

# List the sudo.schema
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn={12}sudo,cn=schema,cn=config

# Verify that the AuditLog is configured.
# ldapsearch -D "cn=admin,cn=config" -w secret -b olcDatabase={1}bdb,cn=config

# List root DN:s, controls, featurs etc.
# ldapsearch -LLL -x  -b "" -s base +

#
# ldapsearch -x -b "dc=syco,dc=net" -e ppolicy objectclass=posixAccount

# List all relevant database options.
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config cn=config
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config schema
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=schema,cn=config
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config olcDatabase={0}config
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config olcDatabase={-1}frontend
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config olcDatabase={1}bdb
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config olcDatabase={2}monitor
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config 'cn=module*'
# ldapsearch -D "cn=Manager,dc=syco,dc=net" -w secret  olcDatabase={2}monitor,cn=config


# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config 'cn=module*'
# ldapsearch -D "cn=admin,cn=config" -w secret -b dc=syco,dc=net cn=default
# ldapsearch -D "cn=admin,cn=config" -w secret -b olcDatabase={1}bdb,cn=config olcOverlay=ppolicy
# ldapsearch -D "cn=admin,cn=config" -w secret -b uid=user4,ou=people,dc=syco,dc=net
# # Return my self.
# ldapsearch -b uid=user1,ou=people,dc=syco,dc=net -D "uid=user1,ou=people,dc=syco,dc=net" -w fratsecret
