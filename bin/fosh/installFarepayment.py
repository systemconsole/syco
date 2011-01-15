#! /usr/bin/env python

#
# Install farepayment into glassfish
#
# https://redmine.fareoffice.com/projects/sysops/wiki/How_to_setup_Farepayment_on_Glassfish_301

import os, time, stat, shutil
import app, general, version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("install-farepayment", install_farepayment, help="Install farepayment on the current server.")  

def install_farepayment(args):  
  global script_version
  app.print_verbose("Install farepayment version: %d" % script_version)
  ver_obj = version.Version()
  if ver_obj.is_executed("InstallFarepayment", script_version):
    app.print_verbose("   Already installed latest version")
    return

  for domain_name, admin_port in [["domain1", "6048"], ["domain2", "7048"]]:
    #_create_password_alias(admin_port)
    _create_database_resources(admin_port)  

  #TODO ver_obj.mark_executed("InstallFarepayment", script_version)  
  
#
# Options / private memembers
#
def _get_mysql_password():
  return "changeme"      

def _create_password_alias(admin_port):
  '''
  A password alias is used to indirectly access a password so that the password itself
  does not appear in cleartext in the domain's domain.xml configuration file.
  
  '${ALIAS=mysql-password}' can be inserted in the domain.xml where mysql connection is configured.
  
  http://docs.sun.com/app/docs/doc/821-1751/ghgqc?l=en&a=view
  
  '''
  general.shell_run("/usr/local/glassfish/bin/asadmin  --port " + admin_port + " create-password-alias mysql-password",
    user="glassfish",
    events={
      '(?i)Enter the alias password> ': _get_mysql_password() + "\n",
      '(?i)Enter the alias password again> ': _get_mysql_password() + "\n"      
    }
  ) 
    
def _create_database_resources(admin_port):
  '''
  Create connection pool to the mysql server.
  
  http://docs.sun.com/app/docs/doc/821-1751/gitxw?l=en&a=view
  
  '''
  mysql_server_name="localhost"
  user="mysql"
  password="${ALIAS=mysql-password}"
  database_name="farepayment"

  mysql_server_name="10.100.50.1"
  user="root"
  password="ferdnand"
  database_name="farepayment_stable"



  pool_name="MySqlPool"
  jdbc_name="jdbc/farepayment"

  exec_asadmin(admin_port, "delete-jdbc-connection-pool --cascade " + pool_name)

  exec_asadmin(admin_port, 
    'create-jdbc-connection-pool ' +
    '--datasourceclassname com.mysql.jdbc.jdbc2.optional.MysqlConnectionPoolDataSource ' +
    '--restype javax.sql.ConnectionPoolDataSource ' +
    '--property "serverName=' + mysql_server_name + ':port=3306:User=' + user + ':Password=' + password + ':characterEncoding=UTF-8:databaseName=' + database_name + '" '+
    pool_name
  )  
  exec_asadmin(admin_port, "create-jdbc-resource --connectionpoolid " + pool_name + " " + jdbc_name)  
  exec_asadmin(admin_port, "list-jdbc-resources")
  
  # http://blogs.sun.com/JagadishPrasath/entry/connection_validation_in_glassfish_jdbc
  exec_asadmin(admin_port, "set domain.resources.jdbc-connection-pool." + pool_name + ".is-connection-validation-required=true")
  exec_asadmin(admin_port, "set domain.resources.jdbc-connection-pool." + pool_name + ".connection-validation-method=auto-commit")

  # Test if connection is established.
  exec_asadmin(admin_port, "get domain.resources.jdbc-connection-pool."+ pool_name + ".*")
  exec_asadmin(admin_port, "ping-connection-pool " + pool_name)
  

#def deploy_farepayment():
#  pass
#  
#  # Checkout from SVN
#  svn checkout
#  
#  # Deploy the farepayment ear
#  /usr/local/glassfish/bin/asadmin undeploy xxxx.ear  
#  /usr/local/glassfish/bin/asadmin deploy xxxx.ear
#  
#  
#  /usr/local/glassfish/bin/asadmin list-applications
#  Deploying in glassfish
#  http://docs.sun.com/app/docs/doc/821-1750?l=en

def exec_asadmin(admin_port, command):  
  return general.shell_exec_p("/usr/local/glassfish/bin/asadmin --port " + admin_port + " " + command, user="glassfish")