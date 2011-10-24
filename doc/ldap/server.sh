#!/bin/sh
#
# This script is based on information from at least the following links.
#   https://help.ubuntu.com/10.04/serverguide/C/openldap-server.html
#   http://home.roadrunner.com/~computertaijutsu/ldap.html
#   http://www.salsaunited.net/blog/?p=74
#   http://www.server-world.info/en/note?os=CentOS_6&p=ldap&f=3
#   http://www.server-world.info/en/note?os=CentOS_6&p=ldap
#   http://linux.die.net/man/5/slapd-config
#   http://eatingsecurity.blogspot.com/2008/11/openldap-security.html
#
# Client certificate docs.
#   http://www.openldap.org/pub/ksoper/OpenLDAP_TLS.html#4.0
#   http://www.openldap.org/faq/data/cache/185.html
#
# SUDO
#   http://eatingsecurity.blogspot.com/2008/10/openldap-continued.html
#   http://www.sudo.ws/sudo/man/1.8.2/sudoers.ldap.man.html
#
# PPolicy
#   http://www.openldap.org/software/man.cgi?query=slapo-ppolicy&sektion=5&apropos=0&manpath=OpenLDAP+2.3-Release
#   http://www.symas.com/blog/?page_id=66
#
# TODO
# * ppolicy
# * authconfig --ldaploadcacert=<URL>   load CA certificate from the URL
# * http://www.michael-hammer.at/blog/ldap_sudo/
# * Try https://docs.fedoraproject.org/en-US/Fedora/15/html/FreeIPA_Guide/index.html
# * http://eatingsecurity.blogspot.com/2008/11/openldap-security.html
# * Kerberos
# * For complexity checking, it's fairly easy to enable and configure pam_cracklib on each client
#    /etc/pam.d/system-auth
#    password  required pam_cracklib.so \
#                       dcredit=-1 ucredit=-1 ocredit=-1 lcredit=0 minlen=8
# * Radius?
#   http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch31_:_Centralized_Logins_Using_LDAP_and_RADIUS#Configuring_RADIUS_for_LDAP 

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
#TODO setenforce 1
#TODO setsebool -P domain_kernel_load_modules 1

# Communication with the LDAP-server needs to be done with domain name, and not
# the ip. This ensures the dns-name is configured.
sed -i '/127.0.0.1/s/ ldap.syco.net//' /etc/hosts
sed -i '/127.0.0.1/s/$/ ldap.syco.net/' /etc/hosts

# Install packages
yum -y install openldap-servers openldap-clients

# Setup iptables (Add destination ip)
iptables -I INPUT -m state --state NEW -p tcp -s 10.100.110.7/24 --dport 636 -j ACCEPT

#
# Setup certificates
#

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

# Enable LDAPS and dispable LDAP
sed -i 's/[#]*SLAPD_LDAPS=.*/SLAPD_LDAPS=yes/g' /etc/sysconfig/ldap
sed -i 's/[#]*SLAPD_LDAP=.*/SLAPD_LDAP=no/g' /etc/sysconfig/ldap
service slapd restart

#
# Install sudo-ldap
#

# Copy the sudo Schema into the LDAP schema repository
sudo cp /usr/share/doc/sudo-1.7.2p2/schema.OpenLDAP /etc/openldap/schema/sudo.schema
restorecon /etc/openldap/schema/sudo.schema

# Create a conversion file for schema
mkdir ~/sudoWork
echo "include /etc/openldap/schema/sudo.schema" > ~/sudoWork/sudoSchema.conf

# Convert the "Schema" to "LDIF".
slapcat -f ~/sudoWork/sudoSchema.conf -F /tmp/ -n0 -s "cn={0}sudo,cn=schema,cn=config" > ~/sudoWork/sudo.ldif

# Remove invalid data.
sed -i "s/{0}sudo/sudo/g" ~/sudoWork/sudo.ldif

# Remove last 8 (invalid) lines.
head -n-8 ~/sudoWork/cn\=sudo.ldif > ~/sudoWork/sudo2.ldif

# Load the schema into the LDAP server
ldapadd -x -D "cn=admin,cn=config" -w secret -f ~/sudoWork/sudo2.ldif

# Add index to sudoers db
ldapadd -x -D "cn=admin,cn=config" -w secret << EOF
dn: olcDatabase={1}bdb,cn=config
changetype: modify
add: olcDbIndex
olcDbIndex: sudoUser    eq
EOF

ldapadd -x -D "cn=admin,cn=config" -w secret -f ~/sudoWork/sudo2.ldif

# List the new schema
ldapsearch -D "cn=admin,cn=config" -w secret -b cn={12}sudo,cn=schema,cn=config

#
# Add users, groups, sudoers. Ie. the dc=syco,dc=net database.
#
ldapadd -D "cn=Manager,dc=syco,dc=net" -w secret  -f manager.ldif

#
# Debug/Testing
#

# Verify the client-cert auth
# openssl s_client -connect localhost:636 -state \
#     -CAfile /etc/openldap/cacerts/ca.crt \
#     -cert /etc/openldap/cacerts/client.pem \
#     -key /etc/openldap/cacerts/client.pem
#ldapsearch -x -D "cn=admin,cn=config" -w secret  -v -d1

# List all info from the dc=syco,dc=net database.
# ldapsearch -D "cn=Manager,dc=syco,dc=net" -w secret -b dc=syco,dc=net

# List all relevant database options.
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config cn=config
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config schema
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config olcDatabase={0}config
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config olcDatabase={-1}frontend
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config olcDatabase={1}bdb
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config olcDatabase={2}monitor
# ldapsearch -D "cn=Manager,dc=syco,dc=net" -w secret  olcDatabase={2}monitor,cn=config

# List all database options.
# ldapsearch -D "cn=admin,cn=config" -w secret -b cn=config

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
