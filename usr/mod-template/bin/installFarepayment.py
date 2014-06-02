#!/usr/bin/env python
'''
Install Farepayment on a glassfish server and on a mysql server.

$ syco install-farepayment [ENVIRONMENT]
Install Farepayment on a Glassfish v3 prepared application server.

$ syco install-farepayment-db [ENVIRONMENT]
Install Farepayment database and users on a mysql server.

ENVIRONMENT
The environment setting can be one of [sandbox|integration|stable|uat|production].

This variable are also controling which   settings that should be used,
also give the Farepayent java application instruction of what kind of
server-environment it's installed on.

For more information about the installation phase the the redmine wiki at
https://redmine.fareoffice.com/projects/sysops/wiki/How_to_setup_Farepayment_on_Glassfish_301

Example:
  # On a glasfish server.
  syco install-farepayment integration

  # On as mysql server.
  syco install-farepayment-db integration

TODO:
* Install mod_sec rules, deny all traffic to other pathes than this.
  http://10.100.130.120:7080/backoffice
  http://10.100.130.120:7080/superadmin
  http://10.100.130.120:7080/diagnostics
  http://10.100.130.120:7080/spp
  http://10.100.130.120:7080/paymentservice

'''

__author__ = "daniel.lindh@fareoffice.com"
__copyright__ = "Copyright 2011, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel@fareoffice.com"
__credits__ = ["Martin Frej"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import time

import app
import config
import general
import installHttpd
import version
from scopen import scOpen
from installGlassfish31 import GLASSFISH_DOMAINS_PATH, asadmin_exec
from installMysql import mysql_exec
from mysql import MysqlProperties
import iptables

SYCO_FO_PATH = app.SYCO_PATH + "usr/syco-private/"

class InstallFarepayment:

  # The version of this module, used to prevent the same script version to be
  # executed more then once on the same host.
  SCRIPT_VERSION = 1

  class Environment(object):
    '''
    Handle what server environment installation should be performed on.

    '''

    _environment = None
    _valid_environments = ["none", "local", "integration", "stable", "uat", "av-prod", "tc-prod"]

    def __setattr__(self, *args):
     raise TypeError("Can't modify immutable Environment instance")

    def __init__(self, environment):
      environment = environment.lower()
      if (environment not in self._valid_environments):
        raise Exception("Invalid environment " + environment)

      # we can no longer use self._environment = environment to store the instance data
      # so we must explicitly call the superclass
      super(InstallFarepayment.Environment, self).__setattr__('_environment', environment)

    def is_integration(self):
      return (self._environment == "integration")

    def is_stable(self):
      return (self._environment == "stable")

    def is_uat(self):
      return (self._environment == "uat")

    def is_av_production(self):
      return (self._environment == "av-prod")

    def is_tc_production(self):
      return (self._environment == "tc-prod")

    def is_production(self):
      return self.is_av_production() or self.is_tc_production()

    _convert = {"sandbox":"local", "integration":"integration", "stable":"qa", "uat":"candidate", "av-prod":"production", "tc-prod":"production"}

    def get_fp_core_environment(self):
      '''
      TODO: When Farepayment code uses the new environment settings, remove convert functionality.

      '''
      return self._convert[self.get_value()]

    def get_value(self):
      return str(self._environment)

  class Properties:
    '''
    Properties used by the installation.

    '''
    # What kind of server is Farepayment installed on.
    # Change to [sandbox|integration|stable|uat|production]
    environment = None

    # Glassfish domain and admin port that should be installed with Farepayment.
    domains = [["domain1", "6048"], ["domain2", "7048"]]

    # User and password to login to svn
    svn_user = "syscon"
    svn_password = None

    # The URL and name for the farepayment-realm ear dependency.
    FAREPAYMENT_REALM_URL = "https://vcs.fareoffice.com/svn/fo/tags/farepayment/realm/1.0.0/farepayment-realm-1.0.0.zip"

    # The URL and name for Farepayment ear.
    FAREPAYMENT_URL = "https://vcs.fareoffice.com/svn/fo/tags/farepayment/main/1.1.3/dist/farepayment-ear-1.1.3.ear"

    # Test database sql script url.
    CREATE_SQL_URL = None # "https://vcs.fareoffice.com/svn/fo/tags/farepayment/main/1.1.3/db/create_db.sql"
    TEST_DATA_SQL_URL = None # "https://vcs.fareoffice.com/svn/fo/tags/farepayment/main/1.1.3/db/create_test_data.sql"

    # Properties for the mysql connection.
    mysql_properties_list = None

    # Initialize the all properties for the mysql connection.
    def init_mysql_properties(self):
      if (self.env.is_integration()):
        mysql_password = app.get_mysql_integration_password()
        self.mysql_properties_list = [
          MysqlProperties("farepayment", "10.100.130.100", "fp_int", mysql_password, "fp_int", ["10.100.130.120"])
        ]

      if (self.env.is_stable()):
        mysql_password = app.get_mysql_stable_password()
        self.mysql_properties_list = [
          MysqlProperties("farepayment", "10.100.130.100", "fp_stable", mysql_password, "fp_stable", ["10.100.130.121"])
        ]

      if (self.env.is_uat()):
        mysql_password = app.get_mysql_uat_password()
        self.mysql_properties_list = [
          MysqlProperties("farepayment", "10.100.130.100", "fp_uat", mysql_password, "fp_uat", ["10.100.130.122"])
        ]

      if (self.env.is_av_production()):
        mysql_password = app.get_mysql_production_password()
        self.mysql_properties_list = [
          MysqlProperties("farepayment", "10.100.120.105", "fp_prod", mysql_password, "fp_prod", ["10.100.120.125", "10.100.110.125"])
        ]

      if (self.env.is_tc_production()):
        mysql_password = app.get_mysql_production_password()
        self.mysql_properties_list = [
          MysqlProperties("farepayment", "10.100.110.105", "fp_prod", mysql_password, "fp_prod", ["10.100.110.125", "10.100.120.125"])
        ]

    def __init__(self, environment):
      '''
      Initialize all properties for installFarepayment, and ask user for all passwords.

      '''
      self.env = InstallFarepayment.Environment(environment)

      # Get SVN password from user.
      self.svn_password = app.get_svn_password()

      self.init_mysql_properties()

  # Properties for installFarepayment
  prop = None

  def install_farepayment(self, args):
    '''
    Install Farepayment on a Glassfish v3 prepared application server.

    '''
    app.print_verbose("Install Farepayment version: %d" % self.SCRIPT_VERSION)

    if (len(args) != 2):
      raise Exception("Invalid arguments. syco install-farepayment [environment]")

    self.prop = InstallFarepayment.Properties(args[1])

    version_obj = version.Version("installFarepayment" + self.prop.env.get_value(), self.SCRIPT_VERSION)
    version_obj.check_executed()

    self.add_iptables_rules()
    iptables.save()
    self._setup_selinux()

    self._create_log_folder()
    self._create_farepayment_folder()

    for domain_name, admin_port in self.prop.domains:
      self._create_security_realm(domain_name, admin_port)
      self._set_farepayment_environment(admin_port)

      for mysql_properties in self.prop.mysql_properties_list:
        general.wait_for_server_to_start(mysql_properties.server, mysql_properties.port)
        self._create_password_alias(admin_port, mysql_properties)
        self._create_database_resource(domain_name, admin_port, mysql_properties)

    # Restart glassfish before deploying farepayment.
    self._restart_glassfish()

    # The deploy might take some time.
    os.environ["AS_ADMIN_READTIMEOUT"] = "100000"
    general.set_config_property("/etc/profile", 'export AS_ADMIN_READTIMEOUT=100000', 'export AS_ADMIN_READTIMEOUT=100000')

    for domain_name, admin_port in self.prop.domains:

      # Wait to deploy farepayment until the fp mysql user/database are online.
      for mysql_properties in self.prop.mysql_properties_list:
        self._wait_for_valid_database_connection(admin_port, mysql_properties)

      self._deploy_farepayment(admin_port)

    self._configure_httpd()
    version_obj.mark_executed()

  def install_farepayment_db(self, args):
    '''
    Install Farepayment database and users on a mysql server.

    '''
    app.print_verbose("Install Farepayment DB version: %d" % self.SCRIPT_VERSION)

    if (len(args) != 2):
      raise Exception("Invalid arguments. syco install-farepayment-db [environment]")

    self.prop = InstallFarepayment.Properties(args[1])

    version_obj = version.Version("installFarepaymentDb" + self.prop.env.get_value(), self.SCRIPT_VERSION)
    version_obj.check_executed()

    mysql_properties = self.prop.mysql_properties_list[0]
    mysql_exec("create database IF NOT EXISTS " + mysql_properties.database, True)

    mysql_exec("DROP USER " + mysql_properties.user_spec, True)
    mysql_exec("GRANT CREATE TEMPORARY TABLES, SELECT, INSERT, UPDATE, DELETE " +
      " ON " + mysql_properties.database + ".*" +
      " TO " + mysql_properties.user_spec_identified_by,
      True
    )

    if self.prop.CREATE_SQL_URL:
      self._mysql_exec_url(mysql_properties, self.prop.CREATE_SQL_URL,
        remote_user=self.prop.svn_user,
        remote_password=self.prop.svn_password
      )

    if self.prop.TEST_DATA_SQL_URL:
      self._mysql_exec_url(mysql_properties, self.prop.TEST_DATA_SQL_URL,
        remote_user=self.prop.svn_user,
        remote_password=self.prop.svn_password
      )

    general.delete_install_dir()
    version_obj.mark_executed()

  #
  # Options / private memembers
  #
  def _mysql_exec_url(self, mysql_properties, url, remote_user=None, remote_password=None):
    '''
    Download a sql-file, uncompress and insert into mysql.

    The url must be to a sql file. ie http://www.ex.com/db.sql

    '''
    # Extract the basename of the url ie. db.sql
    name = os.path.basename(url)

    general.download_file(url, name, remote_user=remote_user, remote_password=remote_password)

    # Run all sql queries in the database defined by mysql_properties.
    mysql_exec("use " + mysql_properties.database + "\n\. " + app.INSTALL_DIR + name, True)

  def _create_log_folder(self):
    '''
    Used by farepayment to log xml requests etc.

    '''

    # The farepayment log can't be on a volume with noexec.
    scOpen("/etc/fstab").replace_ex(
        "/var/log", "noexec[^0-9]*", "defaults"
    )


    if (not os.access("/var/log/farepayment", os.F_OK)):
      general.shell_exec("mkdir /var/log/farepayment")
    general.shell_exec("chown glassfish:glassfishadm /var/log/farepayment")
    general.shell_exec("touch /var/log/farepayment/repository.dat")
    general.shell_exec("chown glassfish:glassfishadm /var/log/farepayment/repository.dat")

  def _create_farepayment_folder(self):
    general.shell_exec("mkdir -p /usr/local/farepayment/etc")
    general.shell_exec("chown -R glassfish:glassfishadm /usr/local/farepayment")

    app.print_verbose("Set environment")
    general.set_config_property("/usr/local/farepayment/etc/environment", "\$\{ENVIRONMENT\}", self.prop.env.get_value())

  def _create_security_realm(self, domain_name, admin_port):
    '''
    Install and configure the farepayment_realm.

    '''
    # Install Realm files.
    farepayment_realm_name = os.path.basename(self.prop.FAREPAYMENT_REALM_URL)
    general.download_file(self.prop.FAREPAYMENT_REALM_URL, farepayment_realm_name,
      remote_user=self.prop.svn_user,
      remote_password=self.prop.svn_password,
      user="glassfish")

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

    '''
    asadmin_exec(
      "create-system-properties com.fareoffice.farepayment.core.environment=" + self.prop.env.get_fp_core_environment(),
      admin_port
    )

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

  def _restart_glassfish(self):
    '''
    Restart glassfish

    '''
    # <property name="Password" value="mysql-password" />
    for domain_name, admin_port in self.prop.domains:
      asadmin_exec("stop-domain " + domain_name)
      asadmin_exec("start-domain " + domain_name)

  def _wait_for_valid_database_connection(self, admin_port, prop):
    '''
    Test if the connection to the mysql database is up and running.

    '''
    app.print_verbose("Wait until fp is installed on database server.", new_line=False)
    while(True):
      result = asadmin_exec("ping-connection-pool " + prop.pool_name, admin_port)
      if ("Command ping-connection-pool executed successfully" in result):
        return True
      time.sleep(10)

  def _deploy_farepayment(self, admin_port):
    '''
    Deploy the farepayment ear to glassfish.

    '''
    farepayment_name = os.path.basename(self.prop.FAREPAYMENT_URL)
    general.download_file(self.prop.FAREPAYMENT_URL, farepayment_name,
      remote_user=self.prop.svn_user,
      remote_password=self.prop.svn_password,
      user="glassfish")

    # Deploy the farepayment ear
    asadmin_exec("undeploy " + os.path.splitext(farepayment_name)[0], admin_port)
    asadmin_exec("deploy " + app.INSTALL_DIR + farepayment_name, admin_port)

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
    general.shell_exec("mkdir -p /etc/httpd/ssl/")
    self._scp_from("root@" + config.general.get_cert_server_ip(), "/etc/syco/ssl/ssl-farepayment", "/etc/httpd/ssl/")

    # Setup apache config.
    general.shell_exec("cp -f " + SYCO_FO_PATH + "var/httpd/conf.d/010-www.farepayment.com.* /etc/httpd/conf.d/")

    # Configure client authentication
    general.shell_exec("mkdir -p /etc/httpd/ssl/ca-client")
    if (self.prop.env.is_production()):
      self._scp_from("root@" + config.general.get_cert_server_ip(), "/etc/syco/ssl/customer-to-fp/prod/ca/ca-fp-prod.crt", "/etc/httpd/ssl/ca-client/")
    else:
      self._scp_from("root@" + config.general.get_cert_server_ip(), "/etc/syco/ssl/customer-to-fp/test/ca/ca-fp-test.crt", "/etc/httpd/ssl/ca-client/")

    general.shell_exec("/usr/sbin/cacertdir_rehash /etc/httpd/ssl/ca-client/")

    # Allow URLS in modsecurity that are used by Farepayment.
    general.shell_exec("echo '\n' >> /etc/httpd/modsecurity.d/modsecurity_crs_10_config_allow_url.data")
    general.shell_exec("cat " + SYCO_FO_PATH + "var/httpd/modsecurity.d/modsecurity_crs_10_config_allow_url.data_append >> /etc/httpd/modsecurity.d/modsecurity_crs_10_config_allow_url.data")
    general.shell_exec("echo '\n/index.html\n/logo-farepayment\n' >> /etc/httpd/modsecurity.d/modsecurity_crs_10_config_allow_url.data")

    installHttpd.set_file_permissions()
    general.shell_exec("/etc/init.d/httpd restart")

  def _setup_selinux(self):
    '''
    Enable apache to do the proxy requests to glassfish.

    '''
    general.shell_exec("semanage port -a -t http_port_t -p tcp 6080")
    general.shell_exec("semanage port -a -t http_port_t -p tcp 7080")

  def add_iptables_rules(self):
    '''
    Setup iptables for Farepayment.

    '''
    app.print_verbose("Setup iptables for farepayment")
    self.remove_iptables_rules()

    # Create farepayment chains.
    iptables.iptables("-N farepayment_in")
    iptables.iptables("-N farepayment_out")
    iptables.iptables("-A syco_input  -p ALL -j farepayment_in")
    iptables.iptables("-A syco_output -p ALL -j farepayment_out")

    # Allow connection direct to glassfish.
    if (not general.grep("/usr/local/farepayment/etc/environment", "prod")):
      iptables.iptables("-A farepayment_in -m state --state NEW -p tcp --dport 6080  -j ACCEPT")
      iptables.iptables("-A farepayment_in -m state --state NEW -p tcp --dport 6048  -j ACCEPT")
      iptables.iptables("-A farepayment_in -m state --state NEW -p tcp --dport 7080  -j ACCEPT")
      iptables.iptables("-A farepayment_in -m state --state NEW -p tcp --dport 7048  -j ACCEPT")

    # Allow connection to Netgiro
    iptables.iptables("-A farepayment_out -m state --state NEW -d test.ws1.netgiro.com -p tcp --dport 443  -j ACCEPT")
    iptables.iptables("-A farepayment_out -m state --state NEW -d test.ws2.netgiro.com -p tcp --dport 443  -j ACCEPT")
    iptables.iptables("-A farepayment_out -m state --state NEW -d ws1.netgiro.com -p tcp --dport 443  -j ACCEPT")
    iptables.iptables("-A farepayment_out -m state --state NEW -d ws2.netgiro.com -p tcp --dport 443  -j ACCEPT")

    # Allow connection to Mysql servers
    iptables.iptables("-A farepayment_out -m state --state NEW  -p tcp --dport 3306  -j ACCEPT")

  def remove_iptables_rules(self):
    iptables.iptables("-D syco_input   -p ALL -j farepayment_in")
    iptables.iptables("-D sycou_output -p ALL -j farepayment_out")
    iptables.iptables("-F farepayment_in")
    iptables.iptables("-X farepayment_in")
    iptables.iptables("-F farepayment_out")
    iptables.iptables("-X farepayment_out")

if __name__ != "__main__":
  install_farepayment_obj = InstallFarepayment()
  def build_commands(commands):
    commands.add("install-farepayment", install_farepayment_obj.install_farepayment, "environment", help="Install Farepayment on a Glassfish v3 prepared application server.")
    commands.add("install-farepayment-db", install_farepayment_obj.install_farepayment_db, "environment", help="Install Farepayment database and users on a mysql server.")

  def iptables_setup():
    if (not os.path.exists('/usr/local/farepayment/etc/environment')):
      return

    install_farepayment_obj.add_iptables_rules()
