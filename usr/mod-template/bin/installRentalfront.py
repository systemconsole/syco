#!/usr/bin/env python
'''
Install Rentalfront ECL and Rentalfront Backstage on a glassfish server and on a mysql server.

$ syco install-rentalfront [ENVIRONMENT]
Install rentalfront on a Glassfish v3 prepared application server.

$ syco install-rentalfront-db [ENVIRONMENT]
Install rentalfront database and users on a mysql server.

ENVIRONMENT
The environment setting can be one of [local|int|stable|uat|nsg-prod|tc-prod].

This variable are also controls which database settings that should be used,
also gives the Rentalfront java application instructions of what kind of
server-environment it's installed on.

For more information about the installation phase the the redmine wiki at
https://redmine.fareoffice.com/projects/sysops/wiki/How_to_setup_rentalfront_on_Glassfish_301
https://redmine.fareoffice.com/projects/ecl/wiki/Installation
https://redmine.fareoffice.com/projects/rf-backstage/wiki/Installation

Example:
  # On a glasfish server.
  syco install-rentalfront int

  # On a mysql server.
  syco install-rentalfront-db int

'''

__author__ = "daniel.lindh@fareoffice.com"
__copyright__ = "Copyright 2011, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel@fareoffice.com"
__credits__ = ["Mattias Hemmingsson"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import time

import app
import config
import general
from general import x
import version
import iptables
from installGlassfish31 import GLASSFISH_DOMAINS_PATH, asadmin_exec
from installMysql import mysql_exec
from installHttpd import set_file_permissions
from mysql import MysqlProperties

SYCO_FO_PATH = app.SYCO_PATH + "usr/syco-private/"

class InstallRentalfront:

  # The version of this module, used to prevent the same script version to be
  # executed more then once on the same host.
  SCRIPT_VERSION = 1

  class Environment(object):
    '''
    Handle what server environment the installation should be performed on.

    This is a mutable class.

    '''
    _environment = None
    _valid_environments = ["local", "int", "stable", "uat", "nsg-prod", "tc-prod"]

    def __setattr__(self, *args):
     raise TypeError("Can't modify immutable Environment instance")

    def __init__(self, environment):
      environment = environment.lower()
      if (environment not in self._valid_environments):
        raise Exception("Invalid environment " + environment)

      # we can no longer use self._environment = environment to store the instance data
      # so we must explicitly call the superclass
      super(InstallRentalfront.Environment, self).__setattr__('_environment', environment)

    def is_integration(self):
      return (self._environment == "int")

    def is_stable(self):
      return (self._environment == "stable")

    def is_uat(self):
      return (self._environment == "uat")

    def is_nsg_production(self):
      return (self._environment == "nsg-prod")

    def is_tc_production(self):
      return (self._environment == "tc-prod")

    def is_production(self):
      return self.is_nsg_production() or self.is_tc_production()

    def get_value(self):
      value = str(self._environment)
      if (self.is_production()):
        value = 'prod'
      return value

    def get_test_code(self):
      '''
      Data sql files are different between prod, uat and dev.

      '''
      if (self.is_production()):
        code = 'prod'
      elif (self.is_uat()):
        code = 'uat'
      else:
        code = 'dev'

      return code

    _convert = {"sandbox":"local", "int":"integration", "stable":"stable", "uat":"uat", "prod":"production"}

    def get_rentalfront_environment(self):
      '''
      TODO: When Rentalfront code uses the new environment settings, remove convert functionality.

      LOCAL | INT | STABLE | UAT | PROD

      '''
      return self._convert[self.get_value()]


  class Properties:
    '''
    Properties used by the installation.

    '''
    # What kind of server is rentalfront installed on.
    # Change to [sandbox|int|stable|uat|prod]
    environment = None

    # Glassfish domain and admin port that should be installed with rentalfront.
    domains = [["domain1", "6048", "6037"], ["domain2", "7048", "7037"]]

    # User and password to login to svn
    svn_user = "syscon"
    svn_password = None

    # The URL and name for the rentalfront realm ear files.
    RFBS_REALM_URL = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/backstage/realm/1.1.0/dist/rentalfront-backstage-realm.zip"

    # The URL and name for rentalfront ear.
    ECL_URL = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/ecl/0.8.2/dist/rentalfront-ecl-0.8.2.ear"
    ECL_TEST_URL = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/ecl-client/1.0.1/dist/rentalfront-xml-client-1.0.1.war"
    RFBS_URL = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/backstage/main/0.8.2/dist/rentalfront-backstage-0.8.2.ear"

    # Test database sql script url.
    RF_ECL_CREATE_SQL_URL    = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/ecl/0.8.1/db/create_db.sql"
    RF_ECL_TEST_DATA_SQL_URL = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/ecl/0.8.1/db/create_ENV_data.sql"

    RF_BS_CREATE_SQL_URL    = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/backstage/main/0.8.1/db/create_db.sql"
    RF_BS_TEST_DATA_SQL_URL = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/backstage/main/0.8.1/db/create_ENV_data.sql"

    RF_STAT_CREATE_SQL_URL    = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/XXX/main/0.8.1/db/create_db.sql"
    RF_STAT_TEST_DATA_SQL_URL = "https://vcs.fareoffice.com/svn/fo/tags/rentalfront/XXX/main/0.8.1/db/create_ENV_data.sql"

    # Properties for the mysql connection.
    mysql_rf_ecl_properties_list = None
    mysql_rf_bs_properties_list = None
    mysql_rf_stat_properties_list = None

    # Initialize the all properties for the mysql connection.
    def init_mysql_properties(self):
      env = self.env.get_value()
      if (not self.env.is_production()):
        mysql_password = app.get_mysql_password(env)
        clients = ["10.100.130.110", "10.100.130.111", "10.100.130.112"]

        self.mysql_rf_ecl_properties_list = [
          MysqlProperties("rf_ecl",  "10.100.130.100", "rf_ecl_" + env, mysql_password, "rf_ecl_" + env, clients),
        ]

        self.mysql_rf_bs_properties_list = [
          MysqlProperties("rf_bs",   "10.100.130.100", "rf_bs_" + env, mysql_password, "rf_bs_" + env, clients)
        ]

        self.mysql_rf_stat_properties_list = [
          MysqlProperties("rf_stat", "10.100.130.100", "rf_stat_" + env, mysql_password, "rf_stat_" + env, clients)
        ]

      elif (self.env.is_nsg_production()):
        mysql_password = app.get_mysql_production_password()
        clients = ["10.100.110.105", "10.100.110.115", "10.100.110.135"]
        self.mysql_rf_ecl_properties_list = [
          MysqlProperties("rf_ecl", "10.100.120.142", "rf_ecl_" + env, mysql_password, "rf_ecl_" + env, clients),
        ]

        self.mysql_rf_bs_properties_list = [
          MysqlProperties("rf_bs", "10.100.120.142", "rf_bs_" + env, mysql_password, "rf_bs_" + env, clients)
        ]

        self.mysql_rf_stat_properties_list = [
          MysqlProperties("rf_stat", "10.100.120.142", "rf_stat_" + env, mysql_password, "rf_stat_" + env, clients)
        ]

      elif (self.env.is_tc_production()):
        mysql_password = app.get_mysql_production_password()
        clients = ["10.100.110.105", "10.100.110.115", "10.100.110.135"]
        self.mysql_rf_ecl_properties_list = [
          MysqlProperties("rf_ecl", "10.100.110.142", "rf_ecl_" + env, mysql_password, "rf_ecl_" + env, clients),
        ]

        self.mysql_rf_bs_properties_list = [
          MysqlProperties("rf_bs", "10.100.110.142", "rf_bs_" + env, mysql_password, "rf_bs_" + env, clients)
        ]

        self.mysql_rf_stat_properties_list = [
          MysqlProperties("rf_stat", "10.100.110.142", "rf_stat_" + env, mysql_password, "rf_stat_" + env, clients)
        ]

    def __init__(self, environment):
      '''
      Initialize all properties for InstallRentalfront, and ask user for all passwords.

      '''
      self.env = InstallRentalfront.Environment(environment)

      # Get SVN password from user.
      self.svn_password = app.get_svn_password()

      self.init_mysql_properties()

  # Properties for InstallRentalfront
  prop = None

  def install_rentalfront(self, args):
    '''
    Install rentalfront on a Glassfish v3 prepared application server.

    '''
    app.print_verbose("Install rentalfront version: %d" % self.SCRIPT_VERSION)

    self._check_arguments(args)
    self._setup_properties(args[1])

    version_obj = version.Version("InstallRentalfront" + self.prop.env.get_value(), self.SCRIPT_VERSION)
    version_obj.check_executed()

    self._setup_application_file_structure()
    self._secure_server()
    self._configure_glassfish_domains()
    self._deploy_applications()
    self._configure_httpd()
    self._install_doc()

    version_obj.mark_executed()

  def install_rentalfront_db(self, args):
    '''
    Install rentalfront database and users on a mysql server.

    '''
    app.print_verbose("Install rentalfront DB version: %d" % self.SCRIPT_VERSION)

    if (len(args) != 2):
      raise Exception("Invalid arguments. syco install-rentalfront-db [environment]")

    self.prop = InstallRentalfront.Properties(args[1])

    version_obj = version.Version("InstallRentalfrontDb" + self.prop.env.get_value(), self.SCRIPT_VERSION)
    version_obj.check_executed()

    self.install_db(
      self.prop.mysql_rf_ecl_properties_list[0],
      self.prop.RF_ECL_CREATE_SQL_URL,
      self.prop.RF_ECL_TEST_DATA_SQL_URL
    )

    self.install_db(
      self.prop.mysql_rf_bs_properties_list[0],
      self.prop.RF_BS_CREATE_SQL_URL,
      self.prop.RF_BS_TEST_DATA_SQL_URL
    )

    # TODO
    # self.install_db(
    #   self.prop.mysql_rf_stat_properties_list[0],
    #   self.prop.RF_STAT_CREATE_SQL_URL,
    #   self.prop.RF_STAT_TEST_DATA_SQL_URL
    # )

    version_obj.mark_executed()

  def install_db(self, mysql_properties, create_db_url, test_data_url):
    if (self._is_db_existing(mysql_properties)):
      app.print_verbose("Datbase %s already exists." % mysql_properties.database)
    else:
      # All databases uses the same filenames for the sql-files. So first delete
      # any possible existing file, to not import the wrong one by mistake.
      general.delete_install_dir()
      self._mysql_create_users(mysql_properties)
      self._mysql_exec_url(create_db_url, mysql_properties)

      code = self.prop.env.get_test_code()
      test_data_url = test_data_url.replace('ENV', code)
      self._mysql_exec_url(test_data_url, mysql_properties)

  def _check_arguments(self, args):
    if (len(args) != 2):
      raise Exception("Invalid arguments. syco install-rentalfront [environment]")

  def _setup_properties(self, environment):
    self.prop = InstallRentalfront.Properties(environment)

  def _secure_server(self):
    self._setup_selinux()

    self.add_rentalfront_iptables_chain()
    iptables.save()

  def _setup_selinux(self):
    '''
    Enable apache to do the proxy requests to glassfish.

    '''
    x("semanage port -a -t http_port_t -p tcp 6080")
    x("semanage port -a -t http_port_t -p tcp 7080")

  def del_rentalfront_iptables_chain(self):
    iptables.iptables("-D syco_input  -p ALL -j rentalfront_in", general.X_OUTPUT_CMD)
    iptables.iptables("-D syco_output -p ALL -j rentalfront_out", general.X_OUTPUT_CMD)
    iptables.iptables("-F rentalfront_in", general.X_OUTPUT_CMD)
    iptables.iptables("-X rentalfront_in", general.X_OUTPUT_CMD)
    iptables.iptables("-F rentalfront_out", general.X_OUTPUT_CMD)
    iptables.iptables("-X rentalfront_out", general.X_OUTPUT_CMD)
    iptables.del_module("nf_conntrack")
    iptables.del_module("nf_conntrack_ftp")

  def add_rentalfront_iptables_chain(self):
    '''
    Setup iptables for rentalfront.

    '''
    self.del_rentalfront_iptables_chain()

    app.print_verbose("Setup iptables for rentalfront")

    # Load modules for FTP
    iptables.add_module("nf_conntrack")
    iptables.add_module("nf_conntrack_ftp")

    # Create rentalfront chains.
    iptables.iptables("-N rentalfront_in")
    iptables.iptables("-N rentalfront_out")
    iptables.iptables("-A syco_input  -p ALL -j rentalfront_in")
    iptables.iptables("-A syco_output -p ALL -j rentalfront_out")

    # Allow connection direct to glassfish.
    if (not general.grep("/usr/local/rentalfront/etc/environment", "prod")):
      iptables.iptables("-A rentalfront_in -m state --state NEW -p tcp --dport 6080  -j ACCEPT")
      iptables.iptables("-A rentalfront_in -m state --state NEW -p tcp --dport 6048  -j ACCEPT")
      iptables.iptables("-A rentalfront_in -m state --state NEW -p tcp --dport 7080  -j ACCEPT")
      iptables.iptables("-A rentalfront_in -m state --state NEW -p tcp --dport 7048  -j ACCEPT")

    # Allow connection to Farepayment
    if (general.grep("/usr/local/rentalfront/etc/environment", "prod")):
      iptables.iptables("-A rentalfront_out -m state --state NEW -d paymentservice.farepayment.com -p tcp --dport 443  -j ACCEPT")
      iptables.iptables("-A rentalfront_out -m state --state NEW -d paymentservice-active-prod-nsg.farepayment.com -p tcp --dport 443  -j ACCEPT")
      iptables.iptables("-A rentalfront_out -m state --state NEW -d paymentservice-active-prod-tc.farepayment.com -p tcp --dport 443  -j ACCEPT")
    else:
      iptables.iptables("-A rentalfront_out -m state --state NEW -d paymentservice-active-uat-tp.farepayment.com -p tcp --dport 443  -j ACCEPT")
      iptables.iptables("-A rentalfront_out -m state --state NEW -d paymentservice-active-stable-tp.farepayment.com -p tcp --dport 443  -j ACCEPT")
      iptables.iptables("-A rentalfront_out -m state --state NEW -d paymentservice-active-integration-tp.farepayment.com -p tcp --dport 443  -j ACCEPT")

    # Allow connection to Mysql servers
    # TODO: Only our mysql servers.
    iptables.iptables("-A rentalfront_out -m state --state NEW  -p tcp --dport 3306  -j ACCEPT")

    # Allow connection to Odyssey
    # Allow connection to google maps.
    # Allow conection captcha
    # TODO: Only the real ip-numbers
    iptables.iptables("-A rentalfront_out -p tcp --dport 80  -j ACCEPT")
    iptables.iptables("-A rentalfront_out -p tcp --dport 443 -j ACCEPT")

    # Allow connection to Enterprise FTP
    iptables.iptables("-A rentalfront_out -m state --state NEW  -p tcp --dport 21  -j ACCEPT")
    iptables.iptables("-A rentalfront_out -m state --state NEW  -p tcp --dport 20  -j ACCEPT")

  def _setup_application_file_structure(self):
    self._create_log_folder()
    self._create_rentalfront_folder()

  def _create_log_folder(self):
    '''
    Used by rentalfront to log xml requests etc.

    '''
    if (not os.access("/var/log/rentalfront", os.F_OK)):
      x("mkdir /var/log/rentalfront")
      x("chown glassfish:glassfishadm /var/log/rentalfront")

  def _create_rentalfront_folder(self):
    x("mkdir -p /usr/local/rentalfront")
    x("mkdir -p /usr/local/rentalfront/etc")

    app.print_verbose("Set environment")
    general.set_config_property("/usr/local/rentalfront/etc/environment", "\$\{ENVIRONMENT\}", self.prop.env.get_value())

    x("chown -R glassfish:glassfishadm /usr/local/rentalfront")

  def _create_rentalfront_domain_folder(self, domain, iiop_port):
    domain_path = "/usr/local/rentalfront/" + domain
    x("cp -fR " + SYCO_FO_PATH + "var/rentalfront " + domain_path + "/")

    app.print_verbose("Set environment in rfbs.ini")
    general.set_config_property(domain_path + "/etc/rfbs.ini", "\$\{ENVIRONMENT\}", self.prop.env.get_rentalfront_environment())
    general.set_config_property(domain_path + "/etc/rfbs.ini", "\$\{REMOTE_PORT\}", iiop_port)

    x("chown -R glassfish:glassfishadm /usr/local/rentalfront")

  def _is_db_existing(self, mysql_properties):
      '''
      Return True if database exists.

      '''
      result = mysql_exec("show databases like '%s'" % mysql_properties.database, True).strip()
      return (result != "")

  def _mysql_create_users(self, mysql_properties):
    '''
    Create a database and a user that can access that database.

    '''
    mysql_exec("create database IF NOT EXISTS " + mysql_properties.database, True)

    # First create a user, then delete it. This to go around the error message
    # generated by DROP USER if user doesn't exist. Should be solved with
    # IF EXISTS, which doesn't exist. http://bugs.mysql.com/bug.php?id=15287
    mysql_exec("GRANT USAGE ON *.* TO %s;" % mysql_properties.user_spec_identified_by, True)
    mysql_exec("DROP USER " + mysql_properties.user_spec, True)

    mysql_exec("GRANT CREATE TEMPORARY TABLES, SELECT, INSERT, UPDATE, DELETE " +
      " ON " + mysql_properties.database + ".*" +
      " TO " + mysql_properties.user_spec_identified_by,
      True
    )

  #
  # Options / private memembers
  #
  def _mysql_exec_url(self, url, mysql_properties):
    '''
    Download a sql-file, uncompress and insert into mysql.

    The url must be to a sql file. ie http://www.ex.com/db.sql

    '''
    # Extract the basename of the url ie. db.sql
    name = os.path.basename(url)

    general.download_file(url, name, remote_user=self.prop.svn_user, remote_password=self.prop.svn_password)

    # Run all sql queries in the database defined by mysql_properties.
    mysql_exec("use " + mysql_properties.database + "\n" +
      "SET foreign_key_checks = 0;\n" +
      "\. " + app.INSTALL_DIR + name + "\n" +
      "SET foreign_key_checks = 1;\n",
      True
    )

  def _configure_glassfish_domains(self):
    for domain_name, admin_port, iiop_port in self.prop.domains:
      self._create_rentalfront_domain_folder(domain_name, iiop_port)
      self._create_rfbs_security_realm(domain_name, admin_port)

      self._set_ecl_environment(admin_port)
      self._configure_ejbs(admin_port)
      self._set_rfbs_environment(domain_name, admin_port)

      for mysql_properties in self.prop.mysql_rf_ecl_properties_list + self.prop.mysql_rf_bs_properties_list + self.prop.mysql_rf_stat_properties_list:
        general.wait_for_server_to_start(mysql_properties.server, mysql_properties.port)
        self._create_password_alias(admin_port, mysql_properties)
        self._create_database_resource(domain_name, admin_port, mysql_properties)

  def _create_rfbs_security_realm(self, domain_name, admin_port):
    '''
    Install and configure the rfbs security realm.

    '''
    # Configure realm in glassfish
    general.set_config_property(GLASSFISH_DOMAINS_PATH + domain_name + "/config/login.conf",
      r"rentalfrontBackstageRealm { com.fareoffice.rentalfront.backstage.realm.v3.RentalfrontBackstageLoginModule required; };",
      r"rentalfrontBackstageRealm { com.fareoffice.rentalfront.backstage.realm.v3.RentalfrontBackstageLoginModule required; };"
    )

    # Install Realm files.
    self._install_realm_file(domain_name, self.prop.RFBS_REALM_URL, "com/fareoffice/rentalfront/backstage")

    # Create realm
    asadmin_exec("delete-auth-realm rentalfront-backstage-realm", admin_port)
    asadmin_exec("create-auth-realm --classname com.fareoffice.rentalfront.backstage.realm.v3.RentalfrontBackstageRealm --property datasource-jndi=jdbc/backstage rentalfront-backstage-realm", admin_port)

  def _install_realm_file(self, domain_name, realm_url, file_path):
    realm_name = os.path.basename(realm_url)
    general.download_file(
      realm_url,
      realm_name,
      remote_user=self.prop.svn_user,
      remote_password=self.prop.svn_password
    )

    os.chdir(app.INSTALL_DIR)
    x("unzip -o " + realm_name, user="glassfish")
    x("rm -rf " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/classes/" + file_path, user="glassfish")
    x("cp -r " + app.INSTALL_DIR + "com " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/classes/", user="glassfish")

  def _set_ecl_environment(self, admin_port):
    '''
    Set systemproperties for rentalfront.

    '''
    # ECL
    asadmin_exec("create-system-properties com.fareoffice.rentalfront.ecl.core.system.environment=" + self.prop.env.get_rentalfront_environment(), admin_port)
    asadmin_exec("create-system-properties com.fareoffice.rentalfront.ecl.dyndoc.wsdl.url=localhost/dynamicdocuments/v1?wsdl", admin_port)

    if (self.prop.env.is_production()):
      asadmin_exec("create-system-properties com.fareoffice.rentalfront.ecl.payment.wsdl.url=\"https\://paymentsevice.farepayment.com/v3?wsdl\"", admin_port)
    else:
      asadmin_exec("create-system-properties com.fareoffice.rentalfront.ecl.payment.wsdl.url=\"https\://paymentsevice-active-uat-tp.farepayment.com/v3?wsdl\"", admin_port)

    asadmin_exec("delete-jvm-options '-Djavax.net.ssl.keyStorePassword'", admin_port)
    asadmin_exec("create-jvm-options '-Djavax.net.ssl.keyStorePassword=" + app.get_glassfish_master_password() + "'", admin_port)
    asadmin_exec("delete-jvm-options '-Djavax.net.ssl.trustStorePassword'", admin_port)
    asadmin_exec("create-jvm-options '-Djavax.net.ssl.trustStorePassword=" + app.get_glassfish_master_password() + "'", admin_port)

  def _configure_ejbs(self, admin_port):
    '''
    For more info
    https://redmine.fareoffice.com/projects/sysops/wiki/Setup_glassfish_3#EJB-settings

    '''

    # Change retry interval to 5 minutes and retry during 24 hours.
    asadmin_exec("set configs.config.server-config.ejb-container.ejb-timer-service.max-redeliveries=300", admin_port)
    asadmin_exec("set configs.config.server-config.ejb-container.ejb-timer-service.redelivery-interval-internal-in-millis=300000", admin_port)

    # Restrict some function calls in Glassfish.
    asadmin_exec("set server.ejb-container.property.disable-nonportable-jndi-names=true", admin_port)

  def _set_rfbs_environment(self, domain_name, admin_port):
    asadmin_exec("create-system-properties com.fareoffice.rentalfront.backstage.properties=/usr/local/rentalfront/" + domain_name + "/etc/rfbs.ini", admin_port)

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
      '--property "serverName=' + prop.server + ':port=3306:User=' + prop.user + ':Password=\$\{ALIAS\=' + prop.password_alias + '\}:characterEncoding=UTF-8:databaseName=' + prop.database + '" ' +
      prop.pool_name,
      admin_port
    )

    asadmin_exec("create-jdbc-resource --connectionpoolid " + prop.pool_name + " " + prop.jdbc_name, admin_port)

    # http://blogs.sun.com/JagadishPrasath/entry/connection_validation_in_glassfish_jdbc
    asadmin_exec("set domain.resources.jdbc-connection-pool." + prop.pool_name + ".connection-validation-method=auto-commit", admin_port)
    asadmin_exec("set domain.resources.jdbc-connection-pool." + prop.pool_name + ".is-connection-validation-required=true", admin_port)

    # What jdbc-resources and connectionpools are configured
    if (app.options.verbose > 1):
      asadmin_exec("get domain.resources.jdbc-connection-pool." + prop.pool_name + ".*", admin_port)
      asadmin_exec("list-jdbc-resources", admin_port)

  def _deploy_applications(self):
    # Restart glassfish before deploying rentalfront.
    self._restart_glassfish()

    # The deploy might take some time.
    os.environ["AS_ADMIN_READTIMEOUT"] = "100000"
    general.set_config_property("/etc/profile", 'export AS_ADMIN_READTIMEOUT=100000', 'export AS_ADMIN_READTIMEOUT=100000')

    for domain_name, admin_port, iiop_port in self.prop.domains:
      # Wait to deploy rentalfront until the rentalfront mysql user/database are online.
      for mysql_properties in self.prop.mysql_rf_ecl_properties_list + self.prop.mysql_rf_bs_properties_list + self.prop.mysql_rf_stat_properties_list:
        self._wait_for_valid_database_connection(admin_port, mysql_properties)

      self._deploy(admin_port, self.prop.ECL_URL)
      if (not self.prop.env.is_production()):
        self._deploy(admin_port, self.prop.ECL_TEST_URL, "rentalfront-xml-client")
      self._deploy(admin_port, self.prop.RFBS_URL)

  def _restart_glassfish(self):
    '''
    Restart glassfish

    '''
    # <property name="Password" value="mysql-password" />
    for domain_name, admin_port, iiop_port in self.prop.domains:
      asadmin_exec("stop-domain " + domain_name)
      asadmin_exec("start-domain " + domain_name)

  def _wait_for_valid_database_connection(self, admin_port, prop):
    '''
    Test if the connection to the mysql database is up and running.

    '''
    app.print_verbose("Wait until rentalfront is installed on database server.", new_line=False)
    while(True):
      result = asadmin_exec("ping-connection-pool " + prop.pool_name, admin_port)
      if ("Command ping-connection-pool executed successfully" in result):
        return True
      time.sleep(10)

  def _deploy(self, admin_port, url, contextroot = ""):
    '''
    Deploy the rentalfront ear to glassfish.

    '''
    name = os.path.basename(url)
    general.download_file(
      url,
      name,
      remote_user=self.prop.svn_user,
      remote_password=self.prop.svn_password)

    # Create context root
    if (contextroot):
      contextroot = " --contextroot " + contextroot + " "

    # Deploy the rentalfront ear
    asadmin_exec("undeploy " + os.path.splitext(name)[0], admin_port)
    asadmin_exec("deploy " + contextroot + app.INSTALL_DIR + name, admin_port)

    # What applications are installed?
    if (app.options.verbose > 1):
      asadmin_exec("list-applications", admin_port)

  def _scp_from(self, server, src, dst):
    general.shell_run("scp -r " + server + ":" + src + " " + dst,
      events={
        'Are you sure you want to continue connecting \(yes\/no\)\?': "YES\n",
        server + "\'s password\:": app.get_root_password() + "\n"
      }
    )

  def _configure_httpd(self):
    # Get all web certificates.
    x("mkdir -p /etc/httpd/ssl/")
    self._scp_from("root@" + config.general.get_cert_server_ip(), "/etc/syco/ssl/ssl-rentalfront", "/etc/httpd/ssl/")

    # Setup apache config.
    x("cp -f " + SYCO_FO_PATH + "var/httpd/conf.d/011-rentalfront.* /etc/httpd/conf.d/")

    # Allow URLS in modsecurity that are used by rentalfront.
    # TODO: Currently disabled in modsecurity install script.
    #x("echo '\n' >> /etc/httpd/modsecurity.d/modsecurity_crs_10_config_allow_url.data")
    #x("cat " + SYCO_FO_PATH + "var/httpd/modsecurity.d/modsecurity_crs_10_config_allow_url.data_append >> /etc/httpd/modsecurity.d/modsecurity_crs_10_config_allow_url.data")
    #x("echo '\n/index.html\n/logo-rentalfront\n' >> /etc/httpd/modsecurity.d/modsecurity_crs_10_config_allow_url.data")

    set_file_permissions()
    x("/etc/init.d/httpd restart")

  def _install_doc(self):
    '''
    Download and install the Rentalfront-xml webservice documentation from SVN.

    Setup automatic download via cron.

    '''
    self._setup_doc_http_password()
    self._clone_doc_from_svn()
    self._setup_doc_cron_download()
    set_file_permissions()

  def _setup_doc_http_password(self):
    x("mkdir /etc/httpd/password")
    # youshallnotpass
    general.set_config_property2("/etc/httpd/password/htpassword", "durinsbane:H2CdK7FU5Zyx2")

  def _get_wget_cmd(self):
    # NOTE: The cut-dirs should match the download path.
    wget_cmd  = "wget -m --no-parent -q --cut-dirs=8 -nH -P /var/www/html/doc/ --user=" + self.prop.svn_user + " "
    wget_cmd += "https://vcs.fareoffice.com/svn/fo/trunk/rentalfront/ecl/fox/docs/Message%20Specifications/"

    return wget_cmd

  def _clone_doc_from_svn(self):
    x("mkdir /var/www/html/doc")
    general.set_config_property("/root/.wgetrc", '.*http-password.*', 'http-password=' + self.prop.svn_password)

    app.print_verbose("Download documentation.")

    x(self._get_wget_cmd())

  def _setup_doc_cron_download(self):
    # Setup automatic checkout from SVN.
    cron_file="/etc/cron.hourly/ws_doc_download.cron"
    general.set_config_property2(cron_file, "#!/bin/bash\n")
    general.set_config_property2(cron_file, "export WGETRC=/root/.wgetrc")
    general.set_config_property2(cron_file, self._get_wget_cmd())
    general.set_config_property2(cron_file, 'find /var/www/html/ -type f -exec chmod 644 {} \;')
    general.set_config_property2(cron_file, 'find /var/www/html/ -type d -exec chmod 755 {} \;')
    general.set_config_property2(cron_file, 'restorecon /var/www/html/')
    x("chmod 755 " + cron_file)
    x("chcon system_u:object_r:bin_t:s0 " + cron_file)

if __name__ != "__main__":
  install_rentalfront_obj = InstallRentalfront()
  def build_commands(commands):
    commands.add("install-rentalfront", install_rentalfront_obj.install_rentalfront, "environment", help="Install rentalfront on a Glassfish v3 prepared application server.")
    commands.add("install-rentalfront-db", install_rentalfront_obj.install_rentalfront_db, "environment", help="Install rentalfront database and users on a mysql server.")

  def iptables_setup():
    if (not os.path.exists('/var/log/rentalfront')):
      return

    install_rentalfront_obj.add_rentalfront_iptables_chain()
