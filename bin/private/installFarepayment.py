#!/usr/bin/env python
'''
Install Farepayment on a glassfish server and on a mysql server.

$ fosh install-farepayment [ENVIRONMENT]
Install Farepayment on a Glassfish v3 prepared application server.


$ fosh install-farepayment-db [ENVIRONMENT]
Install Farepayment database and users on a mysql server.

ENVIRONMENT
The environment setting can be one of [sandbox|integration|stable|qa|production].
The setting control which database settings that should be done, also give the
Farepayent java application instruction of what kind of server it's installed on.

For more information about the installation phase the the redmine wiki at
https://redmine.fareoffice.com/projects/sysops/wiki/How_to_setup_Farepayment_on_Glassfish_301

Examples:
  # On a glasfish server.
  fosh install-farepayment integration

  # On as mysql server.
  fosh install-farepayment-db integration

Changelog:
  2011-01-28 - Daniel Lindh - Version 1.0.0 of installFarepayment completed.

TODO:
* Allow outgoing traffic to netgiro in iptables.
* Install mod_sec rules, deny all traffic to other pathes than this.
  http://10.100.100.130:7080/backoffice
  http://10.100.100.130:7080/superadmin
  http://10.100.100.130:7080/diagnostics
  http://10.100.100.130:7080/spp
  http://10.100.100.130:7080/paymentservice
* Install client cert between php and farepayment.

'''

__author__ = "daniel.lindh@fareoffice.com"
__copyright__ = "Copyright 2011, Fareoffice Car Rental SolutionsAB"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel@fareoffice.com"
__credits__ = ["Martin Frej"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import app, general, version
from installGlassfish import asadmin_exec, GLASSFISH_DOMAINS_PATH
from mysql import MysqlProperties
from installMysql import mysql_exec

class InstallFarepayment:

  # The version of this module, used to prevent the same script version to be
  # executed more then once on the same host.
  SCRIPT_VERSION = 1

  class Properties:
    '''
    Properties used by the installation.

    '''
    # What kind of server is Farepayment installed on.
    # Change to [sandbox|integration|stable|qa|production]
    environment = None

    # Glassfish domain and admin port that should be installed with Farepayment.
    domains = [["domain1", "6048"], ["domain2", "7048"]]

    # User and password to login to svn
    svn_user = "syscon"
    svn_password = None

    # The URL and name for the farepayment-realm ear dependency.
    farepayment_realm_url = "www.fareonline.net/fo/stable/farepayment/realm/1.0.0/farepayment-realm-1.0.0.zip"

    # The URL and name for Farepayment ear.
    farepayment_url = "www.fareonline.net/fo/stable/farepayment/1.1.0/dist/farepayment-ear-1.1.0.ear"

    # Test database sql script url.
    create_sql_url = "www.fareonline.net/fo/stable/farepayment/1.1.0/db/create_db.sql.gz"
    test_data_sql_url = "www.fareonline.net/fo/stable/farepayment/1.1.0/db/create_test_data.sql.gz"

    # Properties for the mysql connection.
    mysql_properties_list = None

    # Initialize the all properties for the mysql connection.
    def init_mysql_properties(self, environment):
      if (self.environment =="integration"):
          mysql_password = app.get_mysql_fp_integration_password()
          self.mysql_properties_list = [
            MysqlProperties("farepayment",           "10.100.100.140", "fp_integration", mysql_password, "farepayment_integration", ["10.100.100.130", "10.100.100.131", "10.100.100.132"]),
            MysqlProperties("farepayment_primary",   "10.100.100.140", "fp_integration", mysql_password, "farepayment_integration", ["10.100.100.130", "10.100.100.131", "10.100.100.132"]),
            MysqlProperties("farepayment_secondary", "10.100.100.141", "fp_integration", mysql_password, "farepayment_integration", ["10.100.100.130", "10.100.100.131", "10.100.100.132"])]

      if (self.environment =="stable"):
          mysql_password = app.get_mysql_fp_stable_password()
          self.mysql_properties_list = [
            MysqlProperties("farepayment",           "10.100.100.140", "fp_stable", mysql_password, "farepayment_stable", ["10.100.100.130", "10.100.100.131", "10.100.100.132"]),
            MysqlProperties("farepayment_primary",   "10.100.100.140", "fp_stable", mysql_password, "farepayment_stable", ["10.100.100.130", "10.100.100.131", "10.100.100.132"]),
            MysqlProperties("farepayment_secondary", "10.100.100.141", "fp_stable", mysql_password, "farepayment_stable", ["10.100.100.130", "10.100.100.131", "10.100.100.132"])]

      if (self.environment =="qa"):
          mysql_password = app.get_mysql_fp_qa_password()
          self.mysql_properties_list = [
          MysqlProperties("farepayment",           "10.100.100.140", "fp_qa", mysql_password, "farepayment_qa", ["10.100.100.130", "10.100.100.131", "10.100.100.132"]),
          MysqlProperties("farepayment_primary",   "10.100.100.140", "fp_qa", mysql_password, "farepayment_qa", ["10.100.100.130", "10.100.100.131", "10.100.100.132"]),
          MysqlProperties("farepayment_secondary", "10.100.100.141", "fp_qa", mysql_password, "farepayment_qa", ["10.100.100.130", "10.100.100.131", "10.100.100.132"])]

      if (self.environment =="production"):
          mysql_password = app.get_mysql_fp_production_password()
          self.mysql_properties_list = [
          MysqlProperties("farepayment",           "10.100.100.140", "fp_production", mysql_password, "farepayment_production", ["10.100.100.130", "10.100.100.131", "10.100.100.132"]),
          MysqlProperties("farepayment_primary",   "10.100.100.140", "fp_production", mysql_password, "farepayment_production", ["10.100.100.130", "10.100.100.131", "10.100.100.132"]),
          MysqlProperties("farepayment_secondary", "10.100.100.141", "fp_production", mysql_password, "farepayment_production", ["10.100.100.130", "10.100.100.131", "10.100.100.132"])]

    def init_properties(self, environment):
      '''
      Initialize all properties for installFarepayment, and ask user for all passwords.

      '''
      self.environment=environment

      # Get SVN password from user.
      svn_password = app.get_svn_password()

      # Add svn login data to the url.
      self.farepayment_realm_url = "https://" + self.svn_user + ":" + svn_password + "@" + self.farepayment_realm_url
      self.farepayment_url       = "https://" + self.svn_user + ":" + svn_password + "@" + self.farepayment_url
      self.create_sql_url        = "https://" + self.svn_user + ":" + svn_password + "@" + self.create_sql_url
      self.test_data_sql_url     = "https://" + self.svn_user + ":" + svn_password + "@" + self.test_data_sql_url

      self.init_mysql_properties(environment)

    def __setattr__(self, name, val):
      '''
      Called when an attribute assignment is attempted, validate properties.

      '''
      if (name == 'environment'):
        val = val.lower()
        if (val not in ["local", "integration", "stable", "qa", "production"]):
          raise Exception("Invalid value for variable: " + name + " with value " + val)

      self.__dict__[name]=val

  # Properties for installFarepayment
  prop = Properties()

  def install_farepayment(self, args):
    '''
    Install Farepayment on a Glassfish v3 prepared application server.

    '''
    app.print_verbose("Install Farepayment version: %d" % self.SCRIPT_VERSION)

    if (len(args) != 2):
      raise Exception("Invalid arguments. fosh install-farepayment [environment]")

    self.prop.init_properties(args[1])

    version_obj=version.Version("installFarepayment" + self.prop.environment, self.SCRIPT_VERSION)
    version_obj.check_executed()

    self._create_log_folder()

    for domain_name, admin_port in self.prop.domains:
      self._create_security_realm(domain_name, admin_port)
      self._set_farepayment_environment(admin_port)

      for mysql_properties in self.prop.mysql_properties_list:
        self._create_password_alias(admin_port, mysql_properties)
        self._create_database_resource(domain_name, admin_port, mysql_properties)

    self._set_database_resource_password_bugfix()

    for domain_name, admin_port in self.prop.domains:
      self._deploy_farepayment(admin_port)
      for mysql_properties in self.prop.mysql_properties_list:
        self._test_database_connections(admin_port, mysql_properties)

    general.delete_install_dir()
    version_obj.mark_executed()

  def install_farepayment_db(self, args):
    '''
    Install Farepayment database and users on a mysql server.

    '''
    app.print_verbose("Install Farepayment DB version: %d" % self.SCRIPT_VERSION)

    if (len(args) != 2):
      raise Exception("Invalid arguments. fosh install-farepayment-db [environment]")

    self.prop.init_properties(args[1])

    version_obj=version.Version("installFarepaymentDb" + self.prop.environment, self.SCRIPT_VERSION)
    version_obj.check_executed()

    mysql_properties=self.prop.mysql_properties_list[0]
    mysql_exec("create database IF NOT EXISTS " + mysql_properties.database, True)

    mysql_exec("DROP USER " + mysql_properties.user_spec, True)
    mysql_exec("GRANT CREATE TEMPORARY TABLES, SELECT, INSERT, UPDATE, DELETE " +
      " ON " + mysql_properties.database + ".*" +
      " TO " + mysql_properties.user_spec_identified_by,
      True
    )

    self._mysql_exec_url(mysql_properties, self.prop.create_sql_url)
    self._mysql_exec_url(mysql_properties, self.prop.test_data_sql_url)

    general.delete_install_dir()
    version_obj.mark_executed()

  #
  # Options / private memembers
  #
  def _mysql_exec_url(self, mysql_properties, url):
    '''
    Download a gziped sql-file, uncompress and insert into mysql.

    The url must be to a gz file. ie http://www.ex.com/db.sql.gz

    '''
    # Extract the basename of the url ie. db.sql.gz
    name = os.path.basename(url)

    general.download_file(url, name)
    os.chdir(app.INSTALL_DIR)
    general.shell_exec("gunzip -f " + name)

    # Remove the .gz from the filename
    name = os.path.splitext(name)[0]

    # Run all sql queries in the database defined by mysql_properties.
    mysql_exec("use " + mysql_properties.database +"\n\. " + app.INSTALL_DIR + name, True)

  def _create_log_folder(self):
    '''
    Used by farepayment to log xml requests etc.

    '''
    general.shell_exec("mkdir /var/log/farepayment")
    general.shell_exec("chown glassfish:glassfishadm /var/log/farepayment")
    general.shell_exec("touch /var/log/farepayment/repository.dat")
    general.shell_exec("chown glassfish:glassfishadm /var/log/farepayment/repository.dat")

  def _create_security_realm(self, domain_name, admin_port):
    '''
    Install and configure the farepayment_realm.

    '''
    # Install Realm files.
    farepayment_realm_name = os.path.basename(self.prop.farepayment_realm_url)
    general.download_file(self.prop.farepayment_realm_url, farepayment_realm_name)

    general.shell_exec("unzip -o " + farepayment_realm_name, user="glassfish")
    os.chdir(app.INSTALL_DIR)
    general.shell_exec("rm -rf " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/classes/com", user="glassfish")
    general.shell_exec("cp -r " + app.INSTALL_DIR + "com " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/classes/", user="glassfish")

    # Configure realm in glassfish
    general.set_config_property(GLASSFISH_DOMAINS_PATH + domain_name + "/config/login.conf",
      r"farepaymentRealm { com.fareoffice.farepayment.realm.FarepaymentLoginModule required; };",
      r"farepaymentRealm { com.fareoffice.farepayment.realm.FarepaymentLoginModule required; };"
    )
    asadmin_exec("delete-auth-realm farepayment-realm", admin_port)
    asadmin_exec("create-auth-realm --classname com.fareoffice.farepayment.realm.FarepaymentRealm --property datasource-jndi=jdbc/farepayment farepayment-realm", admin_port)

  def _set_farepayment_environment(self, admin_port):
    '''
    Set what kind of environment Farepayment is installed in.

    See InstallFarepayment.Properties.environment

    TODO: When Farepayment code uses the new environment settings, remove convert functionality.

    '''
    convert = {"sandbox":"local", "integration":"integration", "stable":"qa", "candidate":"qa", "production":"production"}
    asadmin_exec("create-system-properties com.fareoffice.farepayment.core.environment=" + convert[self.prop.environment], admin_port)

  def _create_password_alias(self, admin_port, prop):
    '''
    A password alias is used to indirectly access a password so that the password itself
    does not appear in cleartext in the domain's domain.xml configuration file.

    '${ALIAS=mysql-password}' can be inserted in the domain.xml where mysql connection is configured.

    '''
    asadmin_exec("delete-password-alias " + prop.password_alias, admin_port)
    asadmin_exec("create-password-alias " + prop.password_alias,
      admin_port,
      events={
        '(?i)Enter the alias password> ': prop.password + "\n",
        '(?i)Enter the alias password again> ': prop.password + "\n"
      }
    )

  def _create_database_resource(self, domain_name, admin_port, prop):
    '''
    Create connection pool and jdbc resource to the mysql server.

    '''
    asadmin_exec("delete-jdbc-connection-pool --cascade " + prop.pool_name, admin_port)

    asadmin_exec(
      'create-jdbc-connection-pool ' +
      '--datasourceclassname com.mysql.jdbc.jdbc2.optional.MysqlConnectionPoolDataSource ' +
      '--restype javax.sql.ConnectionPoolDataSource ' +
      '--property "serverName=' + prop.server + ':port=3306:User=' + prop.user + ':Password=${alias=' + prop.password_alias + '}:characterEncoding=UTF-8:databaseName=' + prop.database + '" '+
      prop.pool_name,
      admin_port
    )

    asadmin_exec("create-jdbc-resource --connectionpoolid " + prop.pool_name + " " + prop.jdbc_name, admin_port)

    # http://blogs.sun.com/JagadishPrasath/entry/connection_validation_in_glassfish_jdbc
    asadmin_exec("set domain.resources.jdbc-connection-pool." + prop.pool_name + ".is-connection-validation-required=true", admin_port)
    asadmin_exec("set domain.resources.jdbc-connection-pool." + prop.pool_name + ".connection-validation-method=auto-commit", admin_port)

    # What jdbc-resources and connectionpools are configured
    if (app.options.verbose > 1):
      asadmin_exec("get domain.resources.jdbc-connection-pool." + prop.pool_name + ".*", admin_port)
      asadmin_exec("list-jdbc-resources", admin_port)

  def _set_database_resource_password_bugfix(self):
    '''
    The create-jdbc-connection-pool strips the ${alias= part of the mysql password,
    so this slow code needs to be used instead.

    # TODO: Might not be needed in future versions of glassfish

    '''
    # <property name="Password" value="mysql-password" />
    for domain_name, admin_port in self.prop.domains:
      asadmin_exec("stop-domain " + domain_name)

      for mysql_properties in self.prop.mysql_properties_list:
        general.set_config_property(GLASSFISH_DOMAINS_PATH + domain_name + "/config/domain.xml",
          r'.*\<property name\=\"Password\" value\=\"' + mysql_properties.password_alias + '\" \/\>',
          r'      <property name="password" value="${ALIAS=' + mysql_properties.password_alias + '}" />'
      )

      asadmin_exec(command="start-domain " + domain_name)

  def _test_database_connections(self, admin_port, prop):
    '''
    Test if the connection to the mysql database is up and running.

    '''
    asadmin_exec("ping-connection-pool " + prop.pool_name, admin_port)

  def _deploy_farepayment(self, admin_port):
    '''
    Deploy the farepayment ear to glassfish.

    '''
    farepayment_name = os.path.basename(self.prop.farepayment_url)
    general.download_file(self.prop.farepayment_url, farepayment_name)

    # Deploy the farepayment ear
    asadmin_exec("undeploy " + app.INSTALL_DIR + farepayment_name, admin_port)
    asadmin_exec("deploy " + app.INSTALL_DIR + farepayment_name, admin_port)

    # What applications are installed?
    if (app.options.verbose > 1):
      asadmin_exec("list-applications", admin_port)

if __name__ != "__main__":
  install_farepayment_obj=InstallFarepayment()
  def build_commands(commands):
    commands.add("install-farepayment",    install_farepayment_obj.install_farepayment,    "environment", help="Install Farepayment on a Glassfish v3 prepared application server.")
    commands.add("install-farepayment-db", install_farepayment_obj.install_farepayment_db, "environment", help="Install Farepayment database and users on a mysql server.")
