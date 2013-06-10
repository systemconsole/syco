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

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2

# NOTE: Remember to change path in "var/glassfish/glassfish-3.1.1"
GLASSFISH_VERSION      = "glassfish-3.1.1"
GLASSFISH_INSTALL_FILE = GLASSFISH_VERSION + ".zip"
GLASSFISH_REPO_URL     = "http://dlc.sun.com.edgesuite.net/glassfish/3.1.1/release/" + GLASSFISH_INSTALL_FILE
GLASSFISH_INSTALL_PATH = "/usr/local/" + GLASSFISH_VERSION + "/"
GLASSFISH_DOMAINS_PATH = GLASSFISH_INSTALL_PATH + "glassfish/domains/"

# The directory where JAVA stores temporary files.
# Default is /tmp, but the partion that dir is stored on is set to "noexec", and
# java requires to exeute code from the java tmp dir.
JAVA_TEMP_PATH = GLASSFISH_INSTALL_PATH + "tmp"

# http://www.oracle.com/technetwork/java/javase/downloads/index.html
JDK_INSTALL_FILE = "jdk-6u37-linux-x64-rpm.bin"
JDK_REPO_URL     = "http://download.oracle.com/otn-pub/java/jdk/6u37-b06/%s" % (JDK_INSTALL_FILE)
JDK_INSTALL_PATH = "/usr/java/jdk1.6.0_37"

# Mysql Connector
# http://ftp.sunet.se/pub/unix/databases/relational/mysql/Downloads/Connector-J/
MYSQL_CONNECTOR_VERSION     = "mysql-connector-java-5.1.18"
MYSQL_CONNECTOR_INTALL_FILE = MYSQL_CONNECTOR_VERSION + ".tar.gz"
MYSQL_CONNECTOR_REPO_URL    = "http://ftp.sunet.se/pub/unix/databases/relational/mysql/Downloads/Connector-J/" + MYSQL_CONNECTOR_INTALL_FILE

# Google Guice
# Is configured in _install_google_guice.

def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-" + GLASSFISH_VERSION, install_glassfish, help="Install " + GLASSFISH_VERSION + " on the current server.")
  commands.add("uninstall-glassfish", uninstall_glassfish, help="Uninstall " + GLASSFISH_VERSION + " servers on the current server.")

def install_glassfish(args):
  '''
  The main installation function.

  '''
  app.print_verbose("Install %s script-version: %d" % (GLASSFISH_VERSION, SCRIPT_VERSION))
  version_obj = version.Version("Install" + GLASSFISH_VERSION, SCRIPT_VERSION)
  version_obj.check_executed()

  try:
    initialize_passwords()

    general.create_install_dir()

    _set_env_vars()

    _install_software()

    iptables.add_glassfish_chain()
    iptables.save()

    for domain_name, port_base in [["domain1", "6000"], ["domain2", "7000"]]:
      admin_port = str(int(port_base) + 48)
      _create_domains(domain_name, port_base)
      _set_domain_passwords(domain_name, admin_port)
      _set_domain_configs(admin_port)
      _set_jvm_options(admin_port)
      _install_domains_plugins(domain_name)

    # Restart to get all options take affect.
    x("/etc/init.d/" + GLASSFISH_VERSION + " stop -an")
    x("/etc/init.d/" + GLASSFISH_VERSION + " start -an")

    version_obj.mark_executed()
  except Exception, error_text:
    app.print_error("Failed to install glassfish")
    app.print_error(error_text)
    traceback.print_exc(file=sys.stdout)

  general.delete_install_dir()

def uninstall_glassfish(args):
  '''
  The main function the glassfish uninstallation.

  '''
  app.print_verbose("Uninstall " + GLASSFISH_VERSION + " version: %d" % SCRIPT_VERSION)

  if (os.access(GLASSFISH_INSTALL_PATH, os.F_OK)):
    os.chdir("/tmp")
    x("/etc/init.d/" + GLASSFISH_VERSION + " stop -an")
    x("rm -rf " + GLASSFISH_INSTALL_PATH)
    x("/sbin/chkconfig --del " + GLASSFISH_VERSION)
    x("rm " + "/etc/init.d/" + GLASSFISH_VERSION)

  if (_is_glassfish_user_installed()):
    # Change dir if some of the rm commands fails, so not everythig will
    # be deleted by mistake.
    x("rm -rf /home/glassfish")
    x("userdel glassfish")
    x("groupdel glassfishadm")

  if (os.access("/usr/java/jdk1.6.0_22", os.F_OK)):
    x("rpm -e sun-javadb-core-10.5.3-0.2")
    x("rpm -e sun-javadb-client-10.5.3-0.2")
    x("rpm -e sun-javadb-demo-10.5.3-0.2")
    x("rpm -e sun-javadb-docs-10.5.3-0.2")
    x("rpm -e sun-javadb-javadoc-10.5.3-0.2")
    x("rpm -e sun-javadb-common-10.5.3-0.2")
    x("rpm -e jdk-1.6.0_22-fcs")

  if (os.access("/usr/java/jdk1.6.0_24", os.F_OK)):
    x("rpm -e sun-javadb-core-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-client-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-demo-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-docs-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-javadoc-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-common-10.6.2-1.1.i386")
    x("rpm -e jdk-1.6.0_24-fcs")
    x("rpm -e jdk-6u24-linux-amd64")

  if (os.access("/usr/java/jdk1.6.0_29", os.F_OK)):
    x("rpm -e sun-javadb-javadoc-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-docs-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-demo-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-client-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-core-10.6.2-1.1.i386")
    x("rpm -e sun-javadb-common-10.6.2-1.1.i386")
    x("rpm -e jdk-6u29-linux-amd64")

  iptables.del_glassfish_chain()
  iptables.save()

  version_obj = version.Version("Install" + GLASSFISH_VERSION, SCRIPT_VERSION)
  version_obj.mark_uninstalled()

#
# Public members
#
# Might be used by other modules.
#

def asadmin_exec(command, admin_port=None, events=None):
  if (admin_port):
    cmd = GLASSFISH_INSTALL_PATH + "bin/asadmin --port " + admin_port + " " + command
  else:
    cmd = GLASSFISH_INSTALL_PATH + "bin/asadmin " + command

  if (events):
    return general.shell_run(cmd, user="glassfish", events=events)
  else:
    return x(cmd, user="glassfish")

#
# Options / private memembers
#

def _is_glassfish_user_installed():
  '''
  Check if glassfish user is installed.

  '''
  for line in open("/etc/passwd"):
    if "glassfish" in line:
      return True
  return False

def initialize_passwords():
  '''
  Initialize all passwords that used by the script.

  This is done in the beginning of the script.
  '''
  app.get_glassfish_master_password()
  app.get_glassfish_admin_password()

def _set_env_vars():
  '''
  Set java path for the currently logged in user.

  '''
  os.environ["JAVA_HOME"] = "/usr/java/latest"
  os.environ["JDK_HOME"] = "/usr/java/latest"
  os.environ["PATH"] = "/usr/java/latest/bin:" + os.environ["PATH"]

  # Set java path for all users on the server.
  scOpen("/etc/profile").remove("export JAVA_HOME=.*")
  scOpen("/etc/profile").add("export JAVA_HOME=/usr/java/latest")

  scOpen("/etc/profile").remove("export JDK_HOME=.*")
  scOpen("/etc/profile").add("export JDK_HOME=/usr/java/latest")

  scOpen("/etc/profile").remove("export PATH=$PATH:/usr/java/latest/bin")
  scOpen("/etc/profile").add("export PATH=$PATH:/usr/java/latest/bin")

def _install_software():
  '''
  Download and install java and glassfish

  '''
  if (not _is_glassfish_user_installed()):
    # Add a new group for glassfish administration.
    # This can be used for all users that should be able to
    # adminitrate glassfish.
    x("groupadd glassfishadm -g 200")

    # Give glassfish it's own user.
    x("adduser -m -r --shell /bin/bash -u200 -g200 glassfish")

  _install_jdk()
  _install_glassfish()

def _install_jdk():
  '''
  Installation of the java sdk.

  '''
  if (not os.access(JDK_INSTALL_PATH, os.F_OK)):
    os.chdir(app.INSTALL_DIR)
    if (not os.access(JDK_INSTALL_FILE, os.F_OK)):
      general.download_file(JDK_REPO_URL, user="glassfish", cookie="gpw_e24=http%3A%2F%2Fwww.oracle.com%2F")

      x("chmod u+rx " + JDK_INSTALL_FILE)

    if (os.access(JDK_INSTALL_FILE, os.F_OK)):
      general.shell_run("./" + JDK_INSTALL_FILE,
        events={
          "ename: ": "A\r\n",
          "Press Enter to continue.....": "\r\n\r\n",
          "timeout":"-1"
        }
      )
    else:
      raise Exception("Not able to download " + JDK_INSTALL_FILE)

def _install_glassfish():
  '''
  Installation of the glassfish application server.

  '''
  if (not os.access(GLASSFISH_INSTALL_PATH + "/glassfish", os.F_OK)):
    os.chdir(app.INSTALL_DIR)
    if (not os.access(GLASSFISH_INSTALL_FILE, os.F_OK)):
      general.download_file(GLASSFISH_REPO_URL, user="glassfish")

    # Create installation dir
    if (not os.access(GLASSFISH_INSTALL_PATH, os.F_OK)):
      x("mkdir -p " + GLASSFISH_INSTALL_PATH)
      x("chmod 770 " + GLASSFISH_INSTALL_PATH)
      x("chown 200:200 " + GLASSFISH_INSTALL_PATH)

    # Set executeion permissions and run the installation.
    if ".zip" in GLASSFISH_INSTALL_FILE:
      install.package("unzip")
      x("unzip " + GLASSFISH_INSTALL_FILE + " -d " + GLASSFISH_INSTALL_PATH, user="glassfish")
      x("mv " + GLASSFISH_INSTALL_PATH + "glassfish3/* " + GLASSFISH_INSTALL_PATH, user="glassfish")
      x("rm -rf " + GLASSFISH_INSTALL_PATH + "glassfish3", user="glassfish")
    else:
      raise Exception("Only installing zip version of glassfish")

    # Install the start script
    # It's possible to do this from glassfish with "asadmin create-service",
    # but our own script is a little bit better. It creates startup log files
    # and has a better "start user" functionality.
    if (not os.access("/etc/init.d/" + GLASSFISH_VERSION, os.F_OK)):
      x("cp " + app.SYCO_PATH + "var/glassfish/" + GLASSFISH_VERSION + " /etc/init.d/" + GLASSFISH_VERSION)
      x("chmod 0755 " + "/etc/init.d/" + GLASSFISH_VERSION)
      x("/sbin/chkconfig --add " + GLASSFISH_VERSION)
      x("/sbin/chkconfig --level 3 " + GLASSFISH_VERSION + " on")

      scOpen("/etc/init.d/" + GLASSFISH_VERSION).replace("${MYSQL_PRIMARY}", config.general.get_mysql_primary_master_ip())
      scOpen("/etc/init.d/" + GLASSFISH_VERSION).replace("${MYSQL_SECONDARY}", config.general.get_mysql_secondary_master_ip())

  if (not os.access(GLASSFISH_DOMAINS_PATH + "domain1/config/domain.xml", os.F_OK)):
    raise Exception("Failed to install " + GLASSFISH_INSTALL_PATH)

  if (not os.access("/etc/init.d/" + GLASSFISH_VERSION, os.F_OK)):
    raise Exception("Failed to install /etc/init.d/" + GLASSFISH_VERSION)

def _create_domains(domain_name, port_base):
  '''
  Creating two domains for each applications, one active and one passive.

  '''
  asadmin_exec("stop-domain " + domain_name)
  asadmin_exec("delete-domain " + domain_name)
  asadmin_exec("create-domain --portbase " + port_base + " --nopassword " + domain_name)

def _set_domain_passwords(domain_name, admin_port):
  '''
  Security configuration

  '''
  asadmin_exec("stop-domain " + domain_name)

  # Change master password, default=empty
  asadmin_exec("change-master-password --savemasterpassword=true " + domain_name,
    admin_port=None,
    events={
      "(?i)Enter the current master password.*": "changeit\n",
      "(?i)Enter the new master password.*": app.get_glassfish_master_password() + "\n",
      "(?i)Enter the new master password again.*": app.get_glassfish_master_password() + "\n"
    }
  )

  # Create new cert for https
  os.chdir(GLASSFISH_DOMAINS_PATH + domain_name + "/config/")
  x("keytool -delete -alias s1as -keystore keystore.jks -storepass '" + app.get_glassfish_master_password() +"'", user="glassfish")
  x(
    'keytool -keysize 2048 -genkey -alias s1as -keyalg RSA -dname "' +
    'CN=' + config.general.get_organization_name() +
    ',O=' + config.general.get_organization_name() +
    ',L=' + config.general.get_locality() +
    ',S=' + config.general.get_state() +
    ',C=' + config.general.get_country_name() +
    '" -validity 3650' +
    " -keypass '" + app.get_glassfish_master_password() + "'" +
    ' -keystore keystore.jks' +
    " -storepass '" + app.get_glassfish_master_password() + "'",
    user="glassfish"
  )
  x("keytool -list -keystore keystore.jks -storepass '" + app.get_glassfish_master_password() + "'", user="glassfish")

  asadmin_exec("start-domain " + domain_name)

  # Change admin password
  asadmin_exec(" change-admin-password",
    admin_port,
    events={
      '(?i)Enter admin user name \[default: admin\]> ': "admin\n",
      '(?i)Enter admin password> ': "\n",
      '(?i)Enter new admin password> ': app.get_glassfish_admin_password() + "\n",
      '(?i)Enter new admin password again> ': app.get_glassfish_admin_password() + "\n"
    }
  )

  # Stores login info for glassfish user in /home/glassfish/.asadminpass
  asadmin_exec("login",
    admin_port,
    events={
      "Enter admin user name \[default: admin\]> ": "admin\n",
      "Enter admin password> ": app.get_glassfish_admin_password() + "\n"
    }
  )

def _set_domain_configs(admin_port):
  #log to syslog
  asadmin_exec("set-log-attributes com.sun.enterprise.server.logging.SyslogHandler.useSystemLogging=true", admin_port)

  # Disable sending x-powered-by in http header (Glassfish obfuscation)
  asadmin_exec("set server.network-config.protocols.protocol.http-listener-1.http.xpowered-by=false", admin_port)
  asadmin_exec("set server.network-config.protocols.protocol.http-listener-2.http.xpowered-by=false", admin_port)
  asadmin_exec("set server.network-config.protocols.protocol.admin-listener.http.xpowered-by=false", admin_port)

  # Disable auto-deployment
  asadmin_exec("set server.admin-service.das-config.autodeploy-enabled=false", admin_port)
  asadmin_exec("set server.admin-service.das-config.dynamic-reload-enabled=false", admin_port)

def _install_domains_plugins(domain_name):
  _install_mysql_connector(domain_name)
  _install_google_guice(domain_name)

def _install_mysql_connector(domain_name):
  '''
  Install mysql connector

  http://www.mysql.com/downloads/connector/j/

  '''
  os.chdir(app.INSTALL_DIR)

  if (not os.access(MYSQL_CONNECTOR_INTALL_FILE, os.F_OK)):
      general.download_file(MYSQL_CONNECTOR_REPO_URL, user="glassfish")
      general.download_file(MYSQL_CONNECTOR_REPO_URL + ".asc", user="glassfish")

  x("gpg --keyserver keyserver.ubuntu.com --recv-keys 5072E1F5", user="glassfish")
  signature = x("gpg --verify " + MYSQL_CONNECTOR_INTALL_FILE + ".asc", user="glassfish")
  if (r'Good signature from "MySQL Release Engineering <mysql-build@oss.oracle.com>"' not in signature):
    raise Exception("Invalid signature.")

  # TODO: Should it be under /ext/?
  x("tar zxf " + MYSQL_CONNECTOR_INTALL_FILE, user="glassfish")
  x("cp " + MYSQL_CONNECTOR_VERSION +"/" + MYSQL_CONNECTOR_VERSION + "-bin.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")


def _install_google_guice(domain_name):
  '''
  Install google guice

  http://code.google.com/p/google-guice/
  http://code.google.com/p/google-guice/downloads/list

  '''
  os.chdir(app.INSTALL_DIR)
  if (not os.access("guice-3.0.zip", os.F_OK)):
    general.download_file("http://google-guice.googlecode.com/files/guice-3.0.zip", user="glassfish")
    x("unzip -oq guice-3.0.zip", user="glassfish")

  x("cp guice-3.0/guice-3.0.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")
  x("cp guice-3.0/guice-assistedinject-3.0.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")
  x("cp guice-3.0/aopalliance.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")
  x("cp guice-3.0/javax.inject.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")

def _set_jvm_options(admin_port):
  '''
  Change JVM Options used by glassfish

  # http://blogs.sun.com/watt/resource/jvm-options-list.html
  # http://www.oracle.com/technetwork/java/javase/tech/vmoptions-jsp-140102.html

  '''
  min_heap = "512m"
  max_heap = "1024m"
  max_perm_heap_size = "512m"

  # List current jvm options
  # Executed to verify the trust of the certificate.
  asadmin_exec("list-jvm-options",
    admin_port,
    events={'(?i)Do you trust the above certificate [y|N] -->': "y\n"}
  )

  # It's a server not a client.
  asadmin_exec("delete-jvm-options -client", admin_port)
  asadmin_exec("create-jvm-options -server", admin_port)

  # Change min and max heap space (ordinary heap = app objects)
  asadmin_exec("delete-jvm-options -Xmx512m", admin_port)
  asadmin_exec("create-jvm-options -Xmx" + max_heap, admin_port)
  asadmin_exec("create-jvm-options -Xms" + min_heap, admin_port)

  # (perm heap = app class definitions)
  asadmin_exec("delete-jvm-options '-XX\:MaxPermSize=192m'", admin_port)
  asadmin_exec("create-jvm-options '-XX\:MaxPermSize=" + max_perm_heap_size + "'", admin_port)

  # http://wikis.sun.com/display/HotSpotInternals/CompressedOops
  asadmin_exec("create-jvm-options '-XX\:+UseCompressedOops'", admin_port)

  # Use optimized versions of Get<Primitive>Field.
  asadmin_exec("create-jvm-options '-XX\:+UseFastAccessorMethods'", admin_port)

  # http://en.wikipedia.org/wiki/Escape_analysis
  asadmin_exec("create-jvm-options '-XX\:+DoEscapeAnalysis'", admin_port)

  # http://www.oracle.com/technetwork/java/javase/tech/vmoptions-jsp-140102.html
  asadmin_exec("create-jvm-options '-XX\:+AggressiveOpts'", admin_port)

  # Get rid of http header field value "server" (Glassfish obfuscation)
  asadmin_exec("create-jvm-options -Dproduct.name=\"\"", admin_port)

  # Security: Disable the stacktrace for SOAP fault message
  asadmin_exec("create-jvm-options -Dcom.sun.xml.ws.fault.SOAPFaultBuilder.disableCaptureStackTrace=true", admin_port)

  #
  # Tell glassfish-gui that it is not allowed to connect to internet.
  # http://java.net/jira/browse/GLASSFISH-14243
  # http://markmail.org/message/7mykjbd5i6mv6ckj?q=sun.enterprise.tools.admingui.NO_NETWORK#query:sun.enterprise.tools.admingui.NO_NETWORK+page:1+mid:fav63oofenom3gxk+state:results
  # http://serverfault.com/questions/103780/how-to-stop-openesb-glassfish-admin-console-from-opening-connection-to-glassfishe
  #
  #    * Regardless of registration state, there will be no popup reminder,
  #      no registration tree node, no registration in common task.
  #    * GlassFish News will not be shown in the tree node nor the common
  #      task page
  #    * The information frame under Common Task page will not be rendered.
  #
  asadmin_exec("create-jvm-options -Dcom.sun.enterprise.tools.admingui.NO_NETWORK=true", admin_port)

  _set_java_temp_dir(admin_port)

def _set_java_temp_dir(admin_port):
  x("mkdir " + JAVA_TEMP_PATH)
  x("chown glassfish:glassfishadm " + JAVA_TEMP_PATH)
  asadmin_exec("create-jvm-options '-Djava.io.tmpdir=" + JAVA_TEMP_PATH + "'", admin_port)
