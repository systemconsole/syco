#!/usr/bin/env python
# -*- coding: utf8 -*-

'''
Install PBK

$ syco install-pbk [ENVIRONMENT]
Install PBK on play framework with a Apache proxy in front.

$ syco install-pbk-db [ENVIRONMENT]
Install PBK database and users on a mysql server.

ENVIRONMENT
The environment setting can be one of [av-prod|tc-prod].

For more information about the installation phase the the redmine wiki at
https://redmine.fareoffice.com/projects/sysops/wiki/PBK

Example:
  # On the PBK server.
  syco install-pbk prod_av version-1.1.1

  # On the mysql server.
  syco install-pbk-db prod_av

'''

__author__ = "Kristofer Borgström"
__copyright__ = "Copyright 2013, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Kristofer Borgström"
__email__ = "kristofer@fareoffice.com"
__credits__ = ["Daniel Lindh, Mattias Hemmingsson"]
__license__ = "???"
__version__ = "1.1.0"
__status__ = "uat"

import os
import time

from os import listdir
from os.path import isfile, join
import app
import config
import general
from general import x
from general import get_install_dir
from general import download_file
from scopen import scOpen
import version
import iptables
from installGlassfish31 import GLASSFISH_DOMAINS_PATH, asadmin_exec
from installMysql import mysql_exec
from installHttpd import set_file_permissions
from httpdUtils import toggle_apache_mod
from mysql import MysqlProperties

SYCO_FO_PATH = app.SYCO_PATH + "usr/syco-private/"

class InstallPbk:

  # The version of this module, used to prevent the same script version to be
  # executed more then once on the same host.
  SCRIPT_VERSION = 4

  env = None
  pbkVersion = None


  class Environment:
    environments = {
      "prod_av" : 1,
      "prod_tc" : 2,
      "uat_av" : 3,
      "uat_tc" : 4,
    }

    def __init__(self, envStr):
      self.id = self.environments[envStr]
      if self.id == None:
        raise Exception("Invalid environment: " + envStr)

      self.name = envStr;


  class Properties:
    '''
    Properties used by the installation.

    '''
    # What kind of server is pbk installed on.
    env = None
    user_spec = ""
    user_spec_identified_by = ""

    JAVA_PACKAGE_URL = "http://packages.fareoffice.com/java/jdk-7u40-linux-x64.tar.gz"
    JAVA_DIR = "/usr/local/jdk1.7.0_40/"

    PLAY_PACKAGE_URL = "http://packages.fareoffice.com/play/play-2.1.1.zip"
    PLAY_DIR = "/opt/play/"
    PLAY_USER = "play"
    PLAY_GROUP = "play"

    PBK_DIR = "/opt/ehi-pbk/"
    PBK_CONF_DIR = "/opt/pbk-conf/"
    PBK_CONTENT_DIR = "/var/www/html/"
    PBK_EVOLUTIONS_DIR = PBK_DIR + "conf/evolutions/default/"
    PBK_STARTUP_SCRIPT = "pbk-start"
    PBK_HTACCESS_DIR = "/opt/pbk-htaccess/"

    # Initialize the all properties for mysql
    PBK_DB_SCHEMA_PREFIX = "pbk"
    PBK_DB_USER_PREFIX = "pbkdbuser"
    PBK_DB_CLIENTS = ["10.101.17.164", "10.101.17.165", "10.101.18.164", "10.101.18.165"]

    def __init__(self, environment):
      '''
      Initialize all properties for InstallPbk, and ask user for all passwords.
      '''

      self.env = environment;
      self.mysql_user = self.PBK_DB_USER_PREFIX + self.getEnvironmentType()
      self.mysql_password = app.get_mysql_password(self.PBK_DB_USER_PREFIX + self.getEnvironmentType())
      self.mysql_db = self.PBK_DB_SCHEMA_PREFIX if self.getEnvironmentType() == "prod" else self.PBK_DB_SCHEMA_PREFIX + "_uat"
      self.rf_prod_mode = "true" if self.getEnvironmentType() == "prod" else "false"
      self.rf_url = "https://ws.fareoffice.com/fox/v1" if self.getEnvironmentType() == "prod" else "https://ws-uat.fareoffice.com/fox/v1"
      self.java_xms = "1024" if self.getEnvironmentType() == "prod" else "256"
      self.java_xmx = "4096" if self.getEnvironmentType() == "prod" else "1024"

      for client in self.PBK_DB_CLIENTS:
        if (len(self.user_spec) > 0):
          self.user_spec += ","
        self.user_spec += "'" + self.PBK_DB_USER_PREFIX + self.getEnvironmentType() + "'@'" + client + "'"

      for client in self.PBK_DB_CLIENTS:
        if (len(self.user_spec_identified_by) > 0):
          self.user_spec_identified_by += ","
        self.user_spec_identified_by += "'" + self.PBK_DB_USER_PREFIX + self.getEnvironmentType()  + "'@'" + client + "' IDENTIFIED BY '" + self.mysql_password + "'"

      self.mysql_primary_master = config.general.get_mysql_primary_master_ip()

    def getEnvironmentType(self):
      if (self.env.name.startswith("prod")):
        return "prod"
      elif (self.env.name.startswith("uat")):
        return "uat"
      else:
        #Other envs not supported yet
        raise Exception("Invalid environment: " + self.env);


  # Properties for InstallPbk
  prop = None

  def install_pbk(self, args):
    '''
    Install PBK
    '''
    app.print_verbose("Install PBK version: %d" % self.SCRIPT_VERSION)

    self._check_arguments(args)
    self._setup_properties(args[1])
    self.pbkVersion = args[2]

    version_obj = version.Version("InstallPbk" + self.prop.env.name, self.SCRIPT_VERSION)
    version_obj.check_executed()

    x("yum -y install git unzip policycoreutils-python")
    self._setup_play_user()
    self._setup_application_file_structure()
    self._setup_selinux()
    self._install_java()
    self._install_play()
    self._configure_play()
    self._install_pbk_files()
    self._compile_pbk()
    self._install_startup_and_start()
    self._configure_httpd()

    version_obj.mark_executed()

  def install_pbk_db(self, args):
    '''
    Install PBK database and users on a mysql server.
    '''
    app.print_verbose("Install PBK DB version: %d" % self.SCRIPT_VERSION)

    if (len(args) != 2):
      raise Exception("Invalid arguments. syco install-pbk-db [environment]")

    self.prop = InstallPbk.Properties(args[1])

    version_obj = version.Version("InstallPbkDb" + self.prop.env.get_value(), self.SCRIPT_VERSION)
    version_obj.check_executed()

    #Install PBK files since the DB evolutions are here
    self._install_pbk_files()
    self.install_db()

    version_obj.mark_executed()

  def install_db(self):

    if self._db_exists():
      app.print_verbose("Database %s already exists." % self.prop.PBK_DB_SCHEMA_PREFIX)
    else:
      # All databases uses the same filenames for the sql-files. So first delete
      # any possible existing file, to not import the wrong one by mistake.
      general.delete_install_dir()
      self._db_create_schema_and_users()
      self._db_apply_evolutions()

  def _db_exists(self):
      '''
      Return True if database exists.

      '''
      result = mysql_exec("show databases like '%s'" % self.prop.PBK_DB_SCHEMA_PREFIX, True).strip()
      return (result != "")

  def _db_create_schema_and_users(self):
    '''
    Create a database and a user that can access that database.
    '''
    mysql_exec("create database IF NOT EXISTS " + self.prop.PBK_DB_SCHEMA_PREFIX, True)

    # First create a user, then delete it. This to go around the error message
    # generated by DROP USER if user doesn't exist. Should be solved with
    # IF EXISTS, which doesn't exist. http://bugs.mysql.com/bug.php?id=15287

    mysql_exec("GRANT USAGE ON *.* TO %s;" % self.prop.user_spec_identified_by, True)
    mysql_exec("DROP USER " + self.prop.user_spec, True)

    mysql_exec("GRANT CREATE TEMPORARY TABLES, SELECT, INSERT, UPDATE, DELETE " +
      " ON " + self.prop.PBK_DB_SCHEMA_PREFIX + ".*" +
      " TO " + self.prop.user_spec_identified_by,
      True
    )

  #
  # Options / private memembers
  #
  def _db_apply_evolutions(self):
    '''
    Run all evolutions files

    '''
    # List all evolutions sql files in lexicographical order
    evolutions = [ f for f in listdir(self.prop.PBK_EVOLUTIONS_DIR) if isfile(join(self.prop.PBK_EVOLUTIONS_DIR, f)) ]
    evolutions.sort()

    # Remove existing ups dir and create it again (to remove any previously generated data)
    ups_dir = self.prop.PBK_EVOLUTIONS_DIR + "ups/"
    x("rm -rf {0}".format(ups_dir))
    x("mkdir -p {0}".format(ups_dir))

    # Extract "Ups" from evolutions files
    for evolution in evolutions:
      #Create an "Ups" file in a subfolder

      output_file = open(ups_dir + evolution, 'w')

      with open(self.prop.PBK_EVOLUTIONS_DIR + evolution) as f:

        #Read SQL queries from "# --- !Ups" to "# --- !Downs"
        do_read_lines = False
        for line in iter(f.readline, ""):
          if (not do_read_lines and "# --- !Ups" in line) :
            do_read_lines = True
            continue

          if (do_read_lines and "# --- !Downs" in line):
            break; #Ignore the downs...

          if do_read_lines:
            output_file.write(line)

    # Run all sql queries in the evolutions files
    for evolution in evolutions:
      mysql_exec("use " + self.prop.PBK_DB_SCHEMA_PREFIX + "\n" +
        "SET foreign_key_checks = 0;\n" +
        "\. " + ups_dir + evolution + "\n" +
        "SET foreign_key_checks = 1;\n",
        True
      )

  def _check_arguments(self, args):
    if (len(args) != 3):
      raise Exception("Invalid arguments. syco install-pbk [environment] [version]")

  def _setup_properties(self, envStr):

    self.prop = InstallPbk.Properties(InstallPbk.Environment(envStr))

  def _setup_selinux(self):
    x("semanage port -a -t http_port_t -p tcp 9000")


  def _install_java(self):

    #Download and extract to the installation dir
    tmp_file = get_install_dir() + "jdk-tar.gz"
    download_file(self.prop.JAVA_PACKAGE_URL, "jdk-tar.gz")
    x("tar -xvzf {0} -C /usr/local".format(tmp_file))

    #Delete any existing java symlinks
    x("rm -f /usr/bin/java")
    x("rm -f /usr/bin/javac")

    #Symlink the executables
    x("ln -s {0}/bin/java /usr/bin/java".format(self.prop.JAVA_DIR))
    x("ln -s {0}/bin/javac /usr/bin/javac".format(self.prop.JAVA_DIR))

  def _install_play(self):

    #Create folder for play
    x("rm -rf " + self.prop.PLAY_DIR)
    x("mkdir -p " + self.prop.PLAY_DIR)

    #Download and extract to the installation dir
    tmp_file = get_install_dir() + "play.zip"
    download_file(self.prop.PLAY_PACKAGE_URL, "play.zip")
    x("/usr/bin/unzip -o {0} -d {1}".format(tmp_file, self.prop.PLAY_DIR))


  def _setup_play_user(self):
    x("groupadd {0}".format(self.prop.PLAY_GROUP))
    x("useradd -m -s /bin/bash -d {0} -g {1} {2}".format(self.prop.PBK_CONF_DIR, self.prop.PLAY_USER, self.prop.PLAY_GROUP))

  def _setup_application_file_structure(self):
    self._create_conf_folder()

  def _create_conf_folder(self):
    '''
    Used for pbk config files.
    '''

    if (not os.access(self.prop.PBK_CONF_DIR, os.F_OK)):
      x("mkdir -p {0}".format(self.prop.PBK_CONF_DIR))
      x("chmod 775 {0}".format(self.prop.PBK_CONF_DIR))


  def _configure_play(self):

    #Copy config files to config directory
    x("cp -f {0}var/pbk/config/* {1}".format(SYCO_FO_PATH, self.prop.PBK_CONF_DIR))
    x("chmod 664 {0}*".format(self.prop.PBK_CONF_DIR))

    #Replace tags in config file
    pbkConfigFile = "{0}installed_application.conf".format(self.prop.PBK_CONF_DIR)
    pbkStartupScript = "/usr/local/sbin/" + self.prop.PBK_STARTUP_SCRIPT

    #Copy content files to content directory
    x("cp -f " + SYCO_FO_PATH + "var/pbk/content/* " + self.prop.PBK_CONTENT_DIR)
    x("chown apache:apache " + self.prop.PBK_CONTENT_DIR +  "*")

    pbk_conf = scOpen(pbkConfigFile)
    pbk_conf.replace("${MYSQL_PRIMARY_MASTER}", self.prop.mysql_primary_master)
    pbk_conf.replace("${MYSQL_USER}", self.prop.mysql_user)
    pbk_conf.replace("${MYSQL_PASSWORD}", self.prop.mysql_password)
    pbk_conf.replace("${MYSQL_DB}", self.prop.mysql_db)
    pbk_conf.replace("${RF_PROD_MODE}", self.prop.rf_prod_mode)
    pbk_conf.replace("${RF_URL}", self.prop.rf_url)

    #Copy start/stop/update scripts to the appropriate directory
    x("cp -f {0}var/pbk/scripts/* /usr/local/sbin/".format(SYCO_FO_PATH, self.prop.PBK_CONF_DIR))

    pbk_startup = scOpen(pbkStartupScript)
    pbk_startup.replace("${JAVA_XMS}", self.prop.java_xms)
    pbk_startup.replace("${JAVA_XMX}", self.prop.java_xmx)

    x("chmod 770 /usr/local/sbin/pbk-*")

  def _install_pbk_files(self):

    #Remove existing folder for PBK
    x("rm -rf " + self.prop.PBK_DIR)
    x("mkdir -p " + self.prop.PBK_DIR)

    #Install git and clone repo
    x("git clone git@github.com:fareoffice/ehi-pbk.git {0}".format(self.prop.PBK_DIR))
    os.chdir(self.prop.PBK_DIR)
    x("git checkout {0}".format(self.pbkVersion))

  def _compile_pbk(self):

    os.chdir(self.prop.PBK_DIR)
    x("/opt/play/play-2.1.1/play clean compile stage")
    x("chown -R {0}:{1} {2}".format(self.prop.PLAY_USER, self.prop.PLAY_GROUP, self.prop.PBK_DIR))

  def _install_startup_and_start(self):
    rc_local = scOpen("/etc/rc.local")
    rc_local.remove("/usr/local/sbin/pbk-start")
    rc_local.add("/usr/local/sbin/pbk-start")

    x("/usr/local/sbin/pbk-start")

  def _configure_httpd(self):
    # Get all web certificates.
    x("mkdir -p /etc/httpd/ssl/")
    self._scp_from("root@" + config.general.get_cert_server_ip(), "/etc/syco/ssl/ssl-pbk", "/etc/httpd/ssl/")

    # Setup apache config.
    x("cp -f " + SYCO_FO_PATH + "var/httpd/conf.d/010-pbk.* /etc/httpd/conf.d/")

    # Enable required modules
    toggle_apache_mod('mod_deflate', True)
    toggle_apache_mod('mod_headers', True)
    toggle_apache_mod('mod_expires', True)

    # Turn on keep-alive - default set to Off, comment this out
    toggle_apache_mod('KeepAlive Off', False)
    
    #Create HTACCESS folder
    x("rm -rf " + self.prop.PBK_HTACCESS_DIR)
    x("mkdir -p " + self.prop.PBK_HTACCESS_DIR)

    #Place .htpasswd file in HTACCESS folder
    x("cp -f {0}var/pbk/htaccess/htpasswd {1}".format(SYCO_FO_PATH, self.prop.PBK_HTACCESS_DIR))
    x("mv /opt/pbk-htaccess/htpasswd /opt/pbk-htaccess/.htpasswd")
    x("chmod 664 {0}.htpasswd".format(self.prop.PBK_HTACCESS_DIR))
    
    x("/etc/init.d/httpd restart")

  def _scp_from(self, server, src, dst):
    general.shell_run("scp -r " + server + ":" + src + " " + dst,
      events={
        'Are you sure you want to continue connecting \(yes\/no\)\?': "YES\n",
        server + "\'s password\:": app.get_root_password() + "\n"
      }
    )


if __name__ != "__main__":
  install_pbk_obj = InstallPbk()
  def build_commands(commands):
    commands.add("install-pbk", install_pbk_obj.install_pbk, "environment", help="Install PBK.")
    #DB install will no longer work - needs updates:
    #UAT & Prod DB install
    #Dont break existing DB
    #DB evolutions no longer used - remove
    #Seperate users for uat/prod db
    #commands.add("install-pbk-db", install_pbk_obj.install_pbk_db, "environment", help="Install PBK database and users on a mysql server.")