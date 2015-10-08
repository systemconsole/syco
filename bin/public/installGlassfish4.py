#!/usr/bin/env python
'''
Install glassfish with optimizations, security and common plugins.

Read more
http://www.oracle.com/technetwork/middleware/glassfish/documentation/index.html
http://glassfish.java.net/
http://www.nabisoft.com/tutorials/glassfish/installing-glassfish-301-on-ubuntu
http://iblog.humani-tech.com/?p=505

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import re
import shutil
import stat
import sys
import traceback
import time

import app
import config
import general
import version
import iptables
import install
from general import x
from scopen import scOpen
import socket

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2

# NOTE: Remember to change path in "var/glassfish/glassfish-3.1.1"
GLASSFISH_VERSION      = "glassfish-4.1"
GLASSFISH_INSTALL_FILE = GLASSFISH_VERSION + ".zip"
GLASSFISH_REPO_URL     = "http://packages.fareoffice.com/glassfish/" + GLASSFISH_INSTALL_FILE
GLASSFISH_INSTALL_PATH = "/usr/local/glassfish4"
GLASSFISH_DOMAINS_PATH = GLASSFISH_INSTALL_PATH + "/glassfish/domains/"
GLASSFISH_USER         = "glassfish"

#Icinga plugins directory
ICINGA_PLUGINS_DIR = "/usr/lib64/nagios/plugins/"

# The directory where JAVA stores temporary files.
# Default is /tmp, but the partion that dir is stored on is set to "noexec", and
# java requires to exeute code from the java tmp dir.
JAVA_TEMP_PATH = GLASSFISH_INSTALL_PATH + "tmp"

# http://www.oracle.com/technetwork/java/javase/downloads/index.html
JDK_INSTALL_FILE = "jdk-8u40-linux-x64.tar.gz"
JDK_REPO_URL     = "http://packages.fareoffice.com/java/%s" % (JDK_INSTALL_FILE)
JDK_INSTALL_PATH = "/usr/java/jdk1.8.0_40"
JDK_VERSION = "jdk1.8.0_40"

# Mysql Connector
# http://ftp.sunet.se/pub/unix/databases/relational/mysql/Downloads/Connector-J/
MYSQL_FILE_NAME="mysql-connector-java-5.1.34"
MYSQL_CONNECTOR_REPO_URL="http://packages.fareoffice.com/mysql-connect/"+MYSQL_FILE_NAME+".tar.gz"


# Google Guice
# Is configured in _install_google_guice.
GUICE_NAME="guice-3.0"
GUICE_URL="http://packages.fareoffice.com/guice/"+GUICE_NAME+".zip"


def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-glassfish4", install_glassfish, help="Install on the current server.")
  commands.add("uninstall-glassfish4", uninstall_glassfish, help="Uninstall  servers on the current server.")


def uninstall_glassfish(args):
  '''
  Uninstalling
  '''
  print "uninstalling"

def install_glassfish(arg):
  '''
  Install glassfish4
  '''
  general.create_install_dir()

  if False ==_is_glassfish_user_installed():
    x("adduser {0}".format(GLASSFISH_USER))

  _install_jdk()
  _install_glassfish()
  _setup_glassfish4()
  _install_mysql_connect()
  _install_guice()
  _install_icinga_ulimit_check(GLASSFISH_USER)
  #
  initialize_passwords()
  _set_domain_passwords()

def _install_icinga_ulimit_check(username):
  nrpe_sudo_path = "/etc/sudoers.d/nrpe"
  common_cfg_path = "/etc/nagios/nrpe.d/common.cfg"
  icinga_script = "check_ulimit.py"

  # Does the checkscript already exist? Otherwise copy it in place.
  if False == os.path.isfile("{0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script)):
    x("cp {0}lib/nagios/plugins_nrpe/{2} {1}{2}".format(app.SYCO_PATH, ICINGA_PLUGINS_DIR, icinga_script))

  # Set permissions and SELinux rules to the checkscript. Can be runned multiple times without problem.
  x("chmod 755 {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script))
  x("chown nrpe:nrpe {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script))
  x("chcon -t nagios_unconfined_plugin_exec_t {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script))
  x("semanage fcontext -a -t nagios_unconfined_plugin_exec_t {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script))

  # Add lines to sudoers, common.cfg if they dont already exist. Can only be runned once.
  nrpe_string_1 = "nrpe ALL=NOPASSWD: {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script)
  nrpe_string_2 = "nrpe ALL=({0}) NOPASSWD: /bin/cat".format(username)
  nrpe_string_3 = "command[check_ulimit_{1}]={0}check_ulimit.py {1} 60 80".format(ICINGA_PLUGINS_DIR, username)

  sudoers_nrpe = open(nrpe_sudo_path, "r+")
  if sudoers_nrpe.read().find(nrpe_string_1) == -1:
    x("echo \"{0}\" >> {1}".format(nrpe_string_1, nrpe_sudo_path))
  if sudoers_nrpe.read().find(nrpe_string_2) == -1:
    x("echo \"{0}\" >> {1}".format(nrpe_string_2, nrpe_sudo_path))
  sudoers_nrpe.close()

  common_cfg = open(common_cfg_path, "r+")
  if common_cfg.read().find(nrpe_string_3) == -1:
    x("echo \"{0}\" >> {1}".format(nrpe_string_3, common_cfg_path))
  common_cfg.close()

  # Finally restart the nrpe service to load the new check.
  x("service nrpe restart")

  '''
  If icinga is configured to check this server with check_ulimit_glassfish it will now get current status.

  '''

def _is_glassfish_user_installed():
  '''
  Check if glassfish user is installed.

  '''
  for line in open("/etc/passwd"):
    if "glassfish" in line:
      return True
  return False

def asadmin_exec(command, admin_port=None, events=None):
  if (admin_port):
    cmd = GLASSFISH_INSTALL_PATH + "/bin/asadmin --port " + admin_port + " " + command
  else:
    cmd = GLASSFISH_INSTALL_PATH + "/bin/asadmin --echo " + command

  if (events):
    return general.shell_run(cmd, user="glassfish", events=events)
  else:
    return x(cmd, user="glassfish")


def _install_jdk():
  '''
  Installation of the java sdk.

  '''
  if (not os.access(JDK_INSTALL_PATH, os.F_OK)):
    os.chdir(app.INSTALL_DIR)
    if (not os.access(JDK_INSTALL_FILE, os.F_OK)):
      general.download_file(JDK_REPO_URL)

      x("chmod u+rx " + JDK_INSTALL_FILE)

    if (os.access(JDK_INSTALL_FILE, os.F_OK)):
          x("tar -zxvf "+JDK_INSTALL_FILE )
          x("mkdir /usr/java")
          x("mv "+JDK_VERSION+" /usr/java")
          x("rm -f /usr/java/default")
          x("rm -f /usr/java/latest")
          x("ln -s /usr/java/"+JDK_VERSION+" /usr/java/default")
          x("ln -s /usr/java/default /usr/java/latest")
          x("chown root:glassfish -R /usr/java/"+JDK_VERSION)
          x("chmod 774 -R /usr/java/"+JDK_VERSION)
          x("chmod 701 /usr/java")
          x("alternatives --install /usr/bin/javac javac /usr/java/latest/bin/javac 20000")
          x("alternatives --install /usr/bin/jar jar /usr/java/latest/bin/jar 20000")
          x("alternatives --install /usr/bin/java java /usr/java/latest/jre/bin/java 20000")
          x("alternatives --install /usr/bin/javaws javaws /usr/java/latest/jre/bin/javaws 20000")




    else:
      raise Exception("Not able to download " + JDK_INSTALL_FILE)

def _install_glassfish():
  '''
  Installation of the glassfish application server.

  '''

  if (not os.access(GLASSFISH_INSTALL_PATH + "/glassfish", os.F_OK)):
    os.chdir(app.INSTALL_DIR)
    if (not os.access(GLASSFISH_INSTALL_FILE, os.F_OK)):
      general.download_file(GLASSFISH_REPO_URL)

    # Set executeion permissions and run the installation.
      x("yum install unzip -y")
      x("unzip " + GLASSFISH_INSTALL_FILE + " -d /usr/local/")
      x("chown glassfish:glassfish -R "+GLASSFISH_INSTALL_PATH)
    else:
      raise Exception("Only installing zip version of glassfish")

    # Install the start script
    # It's possible to do this from glassfish with "asadmin create-service",
    # but our own script is a little bit better. It creates startup log files
    # and has a better "start user" functionality.
    x(GLASSFISH_INSTALL_PATH+"/bin/asadmin create-service")
    x("su glassfish " + GLASSFISH_INSTALL_PATH + "/bin/asadmin start-domain")


def _setup_glassfish4():
  '''
  Setting Glassfish 4 properties
  '''
  asadmin_exec("delete-jvm-options -client")
  asadmin_exec("delete-jvm-options -Xmx512m")
  
  asadmin_exec("create-jvm-options -server")
  asadmin_exec("create-jvm-options -Xmx6144m")
  asadmin_exec("create-jvm-options -Xms1024m")
  asadmin_exec("create-jvm-options -Dhttp.maxConnections=512")
  asadmin_exec("create-jvm-options '-XX\:+AggressiveOpts'")
  asadmin_exec("set server.ejb-container.property.disable-nonportable-jndi-names=true")
  asadmin_exec("set configs.config.server-config.ejb-container.ejb-timer-service.property.reschedule-failed-timer=true")
  asadmin_exec("set-log-attributes com.sun.enterprise.server.logging.SyslogHandler.useSystemLogging=true")
  asadmin_exec("set-log-attributes handlerServices=com.sun.enterprise.server.logging.GFFileHandler,com.sun.enterprise.server.logging.SyslogHandler")
  asadmin_exec("set-log-attributes --target server-config com.sun.enterprise.server.logging.GFFileHandler.formatter=ulf")
  asadmin_exec("set server.admin-service.das-config.autodeploy-enabled=false")
  asadmin_exec("set server.admin-service.das-config.dynamic-reload-enabled=false")
  asadmin_exec("create-system-properties --target server-config com.sun.xml.ws.fault.SOAPFaultBuilder.disableCaptureStackTrace=true")

  #Change product name to hide server information
  asadmin_exec("create-jvm-options -Dproduct.name=warpspeed")

  #Setting monitors levels
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.connector-connection-pool=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.connector-service=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.ejb-container=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.http-service=LOW")
  #asadmin_exec("set server.monitoring-service.module-monitoring-levels.sip-service=LOW")#not available
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.jdbc-connection-pool=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.jms-service=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.jvm=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.orb=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.thread-pool=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.transaction-service=LOW")
  asadmin_exec("set server.monitoring-service.module-monitoring-levels.web-container=LOW")
  
  #Set JMX settings
  asadmin_exec("create-jvm-options -Dcom.sun.management.jmxremote")
  asadmin_exec("create-jvm-options -Dcom.sun.management.jmxremote.port=8686")
  asadmin_exec("create-jvm-options -Dcom.sun.management.jmxremote.local.only=false")
  asadmin_exec("create-jvm-options -Dcom.sun.management.jmxremote.authenticate=false")
  asadmin_exec("create-jvm-options -Dcom.sun.management.jmxremote.ssl=false")
  asadmin_exec("create-jvm-options -Djava.rmi.server.hostname=192.168.0.8")
  
  # Allow glassfish to make more than 32 outgoing connections.
  asadmin_exec("set server.ejb-container.property.thread-core-pool-size=64")
  asadmin_exec("set server.ejb-container.property.thread-max-pool-size=1024")
  asadmin_exec("set server.ejb-container.property.thread-keep-alive-seconds=60")
  asadmin_exec("set server.ejb-container.property.thread-max-pool-size=1024")

  #Increase thread pool sizes
  asadmin_exec("set server.thread-pools.thread-pool.http-thread-pool.max-thread-pool-size=200")
  asadmin_exec("set server.thread-pools.thread-pool.http-thread-pool.min-thread-pool-size=50")
  asadmin_exec("set server.thread-pools.thread-pool.http-thread-pool.max-queue-size=2048")
  asadmin_exec("set server.thread-pools.thread-pool.thread-pool-1.max-thread-pool-size=200")
  asadmin_exec("set server.thread-pools.thread-pool.thread-pool-1.min-thread-pool-size=50")
  asadmin_exec("set server.thread-pools.thread-pool.thread-pool-1.max-queue-size=2048")

  #Increase http acceptor threads, recomended is same as number of cpu cores.
  #Needs to be tested more together with ulimit settings before implementation.
  #asadmin_exec("set server-config.network-config.transports.transport.tcp.acceptor-threads=4")

  #Remove x-powered by to hide server information
  asadmin_exec("set server-config.network-config.protocols.protocol.http-listener-1.http.xpowered-by=false")
  asadmin_exec("set server-config.network-config.protocols.protocol.http-listener-2.http.xpowered-by=false")


def _install_mysql_connect():
  '''
  Install the mysql connect
  '''
  os.chdir(app.INSTALL_DIR)
  general.download_file(MYSQL_CONNECTOR_REPO_URL)
  x("tar -zxvf "+MYSQL_FILE_NAME+".tar.gz")
  x("\cp -f "+MYSQL_FILE_NAME+"/"+MYSQL_FILE_NAME+"-bin.jar "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")
  x("chown glassfish:glassfish -R "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/*")

def _install_guice():
  '''
  Installing guice to glassfish
  '''
  os.chdir(app.INSTALL_DIR)
  general.download_file(GUICE_URL)
  x("unzip "+GUICE_NAME+".zip")
  x("cp "+GUICE_NAME+ "/" +GUICE_NAME+ ".jar "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")
  x("cp "+GUICE_NAME+ "/guice-assistedinject* "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")
  x("cp "+GUICE_NAME+ "/aopalliance* "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")
  x("cp "+GUICE_NAME+ "/javax.inject* "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/")
  x("chown glassfish:glassfish -R "+GLASSFISH_INSTALL_PATH+"/glassfish/domains/domain1/lib/ext/*")
  x("yum remove unzip -y")



def initialize_passwords():
  '''
  Initialize all passwords that used by the script.

  This is done in the beginning of the script.
  '''
  app.get_glassfish_master_password()
  app.get_glassfish_admin_password()

def _set_domain_passwords():
  '''
  Security configuration

  '''
  asadmin_exec("stop-domain")

  # Change master password, default=empty
  asadmin_exec("change-master-password --savemasterpassword=true ",
    admin_port=None,
    events={
      "(?i)Enter the current master password.*": "changeit\n",
      "(?i)Enter the new master password.*": app.get_glassfish_master_password() + "\n",
      "(?i)Enter the new master password again.*": app.get_glassfish_master_password() + "\n"
    }
  )

  # Create new cert for https
  os.chdir(GLASSFISH_DOMAINS_PATH + "/domain1/config/")
  x("/usr/java/latest/bin/keytool -delete -alias gtecybertrust5ca -keystore cacerts.jks -storepass '" + app.get_glassfish_master_password() +"'")
  
  asadmin_exec("start-domain ")

  # Change admin password
  asadmin_exec("change-admin-password",
    admin_port=None,
    events={
      "(?i)Enter admin user name.*": "admin\n",
      "(?i)Enter the admin password.*": "\n",
      "(?i)Enter the new admin password.*": app.get_glassfish_admin_password() + "\n",
      "(?i)Enter the new admin password again.*": app.get_glassfish_admin_password() + "\n"
    }
  )

  # Stores login info for glassfish user in /home/glassfish/.asadminpass
  asadmin_exec("login",
    events={
      "Enter admin user name.*": "admin\n",
      "Enter admin password.*": app.get_glassfish_admin_password() + "\n"
    }
  )

  #Enabling admin on port 4848 from external ip
  asadmin_exec(" --host 127.0.0.1 --port 4848 enable-secure-admin",
    events={
      "Enter admin user name.*": "admin\n",
      "Enter admin password.*": app.get_glassfish_admin_password() + "\n"
    })
  asadmin_exec("stop-domain ")
  asadmin_exec("start-domain ")

