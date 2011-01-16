#! /usr/bin/env python

#
# Install farepayment into glassfish
#
# https://redmine.fareoffice.com/projects/sysops/wiki/How_to_setup_Farepayment_on_Glassfish_301

import os, time, stat, shutil
import app, general, version 
from installGlassfish import exec_asadmin

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
    _create_security_realm(domain_name, admin_port)
    
  return
  
  for domain_name, admin_port in [["domain1", "6048"], ["domain2", "7048"]]:    
    for mysql_properties in app.get_mysql_properties_list():      
      _create_password_alias(admin_port, mysql_properties)
      _create_database_resources(domain_name, admin_port, mysql_properties)

  _set_database_resource_password_bugfix()
  
  for domain_name, admin_port in [["domain1", "6048"], ["domain2", "7048"]]:    
    for mysql_properties in app.get_mysql_properties_list():      
      _test_database_connections(admin_port, mysql_properties)
      
  #TODO ver_obj.mark_executed("InstallFarepayment", script_version)  
  
#
# Options / private memembers
#
def _create_password_alias(admin_port, prop):
  '''
  A password alias is used to indirectly access a password so that the password itself
  does not appear in cleartext in the domain's domain.xml configuration file.
  
  '${ALIAS=mysql-password}' can be inserted in the domain.xml where mysql connection is configured.
  
  http://docs.sun.com/app/docs/doc/821-1751/ghgqc?l=en&a=view
  
  '''
  general.shell_exec_p("/usr/local/glassfish/bin/asadmin  --port " + admin_port + " delete-password-alias " + prop.password_alias, user="glassfish")
  
  general.shell_run("/usr/local/glassfish/bin/asadmin  --port " + admin_port + " create-password-alias " + prop.password_alias,
    user="glassfish",
    events={
      '(?i)Enter the alias password> ': prop.password + "\n",
      '(?i)Enter the alias password again> ': prop.password + "\n"      
    }
  )   
      
def _create_database_resources(domain_name, admin_port, prop):
  '''
  Create connection pool and jdbc resource to the mysql server.
  
  http://docs.sun.com/app/docs/doc/821-1751/gitxw?l=en&a=view
  
  '''
  exec_asadmin(admin_port, "delete-jdbc-connection-pool --cascade " + prop.pool_name)

  exec_asadmin(admin_port, 
    'create-jdbc-connection-pool ' +
    '--datasourceclassname com.mysql.jdbc.jdbc2.optional.MysqlConnectionPoolDataSource ' +
    '--restype javax.sql.ConnectionPoolDataSource ' +
    '--property "serverName=' + prop.server + ':port=3306:User=' + prop.user + ':Password=${alias=' + prop.password_alias + '}:characterEncoding=UTF-8:databaseName=' + prop.database + '" '+
    prop.pool_name
  )  
    
  exec_asadmin(admin_port, "create-jdbc-resource --connectionpoolid " + prop.pool_name + " " + prop.jdbc_name)
  exec_asadmin(admin_port, "list-jdbc-resources")
  
  # http://blogs.sun.com/JagadishPrasath/entry/connection_validation_in_glassfish_jdbc
  exec_asadmin(admin_port, "set domain.resources.jdbc-connection-pool." + prop.pool_name + ".is-connection-validation-required=true")
  exec_asadmin(admin_port, "set domain.resources.jdbc-connection-pool." + prop.pool_name + ".connection-validation-method=auto-commit")

  # Test if connection is established.
  #exec_asadmin(admin_port, "get domain.resources.jdbc-connection-pool."+ prop.pool_name + ".*")

def _set_database_resource_password_bugfix():
  '''
  The above create-jdbc-connection-pool strips the ${alias= part of the mysql password,
  so this slow code needs to be used instead.
  
  # TODO: Might not be needed in future versions of glassfish
  
  '''  
  # <property name="Password" value="mysql-password" />
  for domain_name, admin_port in [["domain1", "6048"], ["domain2", "7048"]]:    
    exec_asadmin(command="stop-domain " + domain_name)

    for prop in app.get_mysql_properties_list():        
      general.set_config_property("/usr/local/glassfish/glassfish/domains/" + domain_name + "/config/domain.xml",
        r'.*\<property name\=\"Password\" value\=\"' + prop.password_alias + '\" \/\>',   
        r'      <property name="password" value="${ALIAS=' + prop.password_alias + '}" />'
    ) 
  
    exec_asadmin(command="start-domain " + domain_name)

def _test_database_connections(admin_port, prop):
  exec_asadmin(admin_port, "ping-connection-pool " + prop.pool_name)    

def _create_security_realm(domain_name, admin_port):

  '''
  TODO
Copy all *.class files inside the Farepayment realm project into <glassfish domain dir>/lib/classes/. Make sure the directory structure is preserved. Typically the files are located in:
- /com/fareoffice/farepayment/realm/
- /com/fareoffice/farepayment/realm/locators/
- /com/fareoffice/farepayment/realm/logger/
- /com/fareoffice/farepayment/realm/util/
  '''
  
  general.set_config_property("/usr/local/glassfish/glassfish/domains/" + domain_name + "/config/login.conf",
    r"farepaymentRealm { com.fareoffice.farepayment.realm.FarepaymentLoginModule required; };",
    r"farepaymentRealm { com.fareoffice.farepayment.realm.FarepaymentLoginModule required; };"
  )
  exec_asadmin(admin_port, "delete-auth-realm farepayment-realm")
  exec_asadmin(admin_port, "create-auth-realm --classname com.fareoffice.farepayment.realm.FarepaymentRealm --property datasource-jndi=jdbc/farepayment farepayment-realm")

  # Get from config file.
  #[local|integration|qa|candidate|production]
  exec_asadmin(admin_port, "create-system-properties com.fareoffice.farepayment.core.environment=integration")  
  
def deploy_farepayment():
  pass
  
  # Checkout from SVN
  # svn checkout
  
  # Deploy the farepayment ear
  #exec_asadmin(admin_port, "undeploy xxxx.ear")
  #exec_asadmin(admin_port, "deploy xxxx.ear")    
  
#  /usr/local/glassfish/bin/asadmin list-applications
#  Deploying in glassfish
#  http://docs.sun.com/app/docs/doc/821-1750?l=en
