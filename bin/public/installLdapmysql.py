#!/usr/bin/env python
'''
Ldap server with mysql backend

'''

__author__ = "Mattias.hemmingsson@fareoffice.com, daniel@cybercow.se"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

from general import x,download_file,generate_password
import scopen
import app
import config
import version
import string


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("install-ldapmysql", install_ldapmysql, help="Install Openldap server with mysql backend")
    commands.add("unistall-ldapmysql", unistall_ldapmysql, help="Uninstall Openldap Server with mysql backend")
    commands.add("update-db-ldapmysql", update-db, help="Reinstall the db")


def install_ldapmysql(args):
    '''
    Install and configure openldap server with mysql backend

    '''
    if os.path.exists("/etc/openldap/slapd.conf"):

      print("There is a slapd-config file will not install")

    else:
      '''
      No configfile move on
      '''
      password =  generate_password(length=16,chars=string.letters + string.digits)
      x('yum install wget make gcc  mysql-devel unixODBC-devel groff -y')
      os.chdir('/opt')
      x('wget ftp://mirror.switch.ch/mirror/OpenLDAP/openldap-release/openldap-2.4.43.tgz')
      x('tar zxvf openldap-*.tgz')
      x('rm -rf  openldap-*.tgz')
      x('mv openldap-* openldap')
      os.chdir('/opt/openldap')
      os.system('./configure --prefix=/usr --exec-prefix=/usr --bindir=/usr/bin --sbindir=/usr/sbin --sysconfdir=/etc --datadir=/usr/share --localstatedir=/var --mandir=/usr/share/man --infodir=/usr/share/info --enable-sql --disable-bdb --disable-ndb --disable-hdb')
      os.system('make depend')
      os.system('make')
      os.system('make install')
      x('\cp -f {0}var/ldap/slapd.conf /etc/openldap/slapd.conf'.format(app.SYCO_PATH))
      x("sed -i 's/SQL_PASS/{0}/g' /etc/openldap/slapd.conf".format(password))
      
    

      
      #Install mysql 
      x('yum install mysql-connector-odbc -y')
      x('odbcinst -j')
      x('\cp -f {0}var/ldap/odbc.ini /etc/odbc.ini'.format(app.SYCO_PATH))
      x("sed -i 's/SQL_PASS/{0}/g' /etc/odbc.ini".format(password))
      x('\cp -f {0}usr/syco-private/var/ldap/init-user.sql /tmp/init-user.sql'.format(app.SYCO_PATH))
      x('\cp -f {0}usr/syco-private/var/ldap/init-db.sql /tmp/init-db.sql'.format(app.SYCO_PATH))	
      x("sed -i 's/SQL_PASS/{0}/g' /tmp/init-sql.user".format(password))
      x('yum install mysql-server -y')
      x('service mysqld restart')
      x('mysql < /tmp/init-user.sql')
      x('mysql < /tmp/init-db.sql')
      x("rm -rf /tmp/init-user.sql")
      x("rm -rf /tmp/init-db.sql")

      #Starting
      x('\cp -f {0}var/ldap/slapd /etc/init.d/slapd'.format(app.SYCO_PATH))
      x('chmod +x /etc/init.d/slapd')
      x('chkconfig --add slapd')
      x('chkconfig slapd on')
      x('/etc/init.d/slapd start')

      
def update_db():
     x('\cp -f {0}usr/syco-private/var/ldap/init-db.sql /tmp/init-db.sql'.format(app.SYCO_PATH))
     x('mysql < /tmp/init-db.sql')
     x("rm -rf /tmp/init-db.sql")
     x('/etc/init.d/slapd restart')


def unistall_ldapmysql(args):
  '''
  Uninstall unistall_ldapmysql

  '''
  print "removing"
  x('service mysql stop')
  x('rm -rf /var/lib/mysql')
  x('rm -f /etc/openlda/slapd.conf')
  
