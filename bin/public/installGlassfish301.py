#!/usr/bin/env python
'''
Install glassfish with optimizations, security and common plugins.

Read more
http://docs.sun.com/app/docs/coll/1343.13?l=en
http://docs.sun.com/app/docs/doc/821-1757/aboaa?l=en&a=view
http://docs.sun.com/app/docs/doc/821-1751?l=en
http://www.nabisoft.com/tutorials/glassfish/installing-glassfish-301-on-ubuntu
http://iblog.humani-tech.com/?p=505
http://www.java.net/forums/glassfish/glassfish

TODO
See installGlassfish31.py

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

import app
import general
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

# NOTE: Remember to change path in
# var/glassfish/glassfish
# var/glassfish-3.0.1-unix-answer
GLASSFISH_VERSION = "glassfish-3.0.1"
GLASSFISH_PATH = "/usr/local/" + GLASSFISH_VERSION + "/"
GLASSFISH_DOMAINS_PATH = GLASSFISH_PATH + "glassfish/domains/"

#GLASSFISH_INSTALL_FILE = "glassfish-3.0.1-unix.sh"
#GLASSFISH_REPO_URL="http://download.java.net/glassfish/3.0.1/release/" + GLASSFISH_INSTALL_FILE

GLASSFISH_INSTALL_FILE = "glassfish-3.0.1.zip"
GLASSFISH_REPO_URL="http://download.java.net/glassfish/3.0.1/release/" + GLASSFISH_INSTALL_FILE

# http://www.oracle.com/technetwork/java/javase/downloads/index.html
JDK_INSTALL_PATH = "/usr/java/jdk1.6.0_24"
JDK_INSTALL_FILE = "jdk-6u24-linux-x64-rpm.bin"
JDK_REPO_URL = "http://" + app.get_installation_server_ip() + "/cobbler/repo_mirror/" + JDK_INSTALL_FILE

# Mysql Connector
# http://ftp.sunet.se/pub/unix/databases/relational/mysql/Downloads/Connector-J/
MYSQL_CONNECTOR_VERSION  = "mysql-connector-java-5.1.15"
MYSQL_CONNECTOR_FILE     = MYSQL_CONNECTOR_VERSION + ".tar.gz"
MYSQL_CONNECTOR_REPO_URL = "http://ftp.sunet.se/pub/unix/databases/relational/mysql/Downloads/Connector-J/" + MYSQL_CONNECTOR_FILE

def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

  '''
  commands.add("install-" + GLASSFISH_VERSION, install_glassfish, help="Install " + GLASSFISH_VERSION + " on the current server.")
  
def install_glassfish(args):
  '''
  The main installation function the for the glassfish, dependencies and plugins.

  '''
  app.print_verbose("Install glassfish3 version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("Install" + GLASSFISH_VERSION, SCRIPT_VERSION)
  version_obj.check_executed()

  try:

    general.create_install_dir()

    # Set java path for the currently logged in user.
    os.environ["JAVA_HOME"] = "/usr/java/latest"
    os.environ["JDK_HOME"] = "/usr/java/latest"
    os.environ["PATH"] = "/usr/java/latest/bin:" + os.environ["PATH"]

    # Set java path for all users on the server.
    general.set_config_property("/etc/profile", 'export JAVA_HOME=/usr/java/latest', 'export JAVA_HOME=/usr/java/latest')
    general.set_config_property("/etc/profile", 'export JDK_HOME=/usr/java/latest', 'export JDK_HOME=/usr/java/latest')
    general.set_config_property("/etc/profile", 'export PATH=$PATH:/usr/java/latest/bin', 'export PATH=$PATH:/usr/java/latest/bin')

    #_set_iptables()
    _install_software()

    for domain_name, port_base in [["domain1", "6000"], ["domain2", "7000"]]:
      admin_port = str(int(port_base) + 48)
      _create_domains(domain_name, port_base)
      _set_domain_passwords(domain_name, admin_port)
      _set_domain_configs(admin_port)
      _set_jvm_options(admin_port)
      _install_domains_plugins(domain_name)

    # Restart to take effect
    general.shell_exec("/etc/init.d/" + GLASSFISH_VERSION + " restart")

    _update_glassfish()

    version_obj.mark_executed()
  except Exception, error_text:
    app.print_error("Failed to install glassfish")
    app.print_error(error_text)
    traceback.print_exc(file=sys.stdout)

  general.delete_install_dir()

def uninstall_glassfish():
  '''
  The main function the glassfish uninstallation.
  
  This function is executed from installGlassfish31

  '''
  app.print_verbose("Uninstall " + GLASSFISH_VERSION + " version: %d" % SCRIPT_VERSION)

  if (os.access(GLASSFISH_PATH, os.F_OK)):
    os.chdir("/tmp")
    general.shell_exec("/etc/init.d/" + GLASSFISH_VERSION + " stop")
    general.shell_exec("rm -rf " + GLASSFISH_PATH)
    general.shell_exec("chkconfig --del " + GLASSFISH_VERSION)
    general.shell_exec("rm " + "/etc/init.d/" + GLASSFISH_VERSION)

  version_obj = version.Version("Install" + GLASSFISH_VERSION, SCRIPT_VERSION)
  version_obj.mark_uninstalled()
#
# Public members
#
# Might be used by other modules.
#

def asadmin_exec(command, admin_port=None, events=None):
  if (admin_port):
    cmd = GLASSFISH_PATH + "bin/asadmin --port " + admin_port + " " + command
  else:
    cmd = GLASSFISH_PATH + "bin/asadmin " + command

  if (events):
    return general.shell_run(cmd, user="glassfish", events=events)
  else:
    return general.shell_exec(cmd, user="glassfish")

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

def _install_software():
  '''
  Download and install java and glassfish

  '''
  if (not _is_glassfish_user_installed()):
    # Add a new group for glassfish administration.
    # This can be used for all users that should be able to
    # adminitrate glassfish.
    general.shell_exec("groupadd glassfishadm -g 550")

    # Give glassfish it's own user.
    general.shell_exec("adduser -m -r --shell /bin/bash -u150 -g550 glassfish")

  _install_jdk()
  _install_glassfish()
  _install_eclipselink()

def _install_jdk():
  '''
  Installation of the java sdk.

  '''
  if (not os.access(JDK_INSTALL_PATH, os.F_OK)):
    os.chdir(app.INSTALL_DIR)
    if (not os.access(JDK_INSTALL_FILE, os.F_OK)):
      general.download_file(JDK_REPO_URL, user="glassfish")
      os.chmod(JDK_INSTALL_FILE, stat.S_IXUSR | stat.S_IRUSR)

    if (os.access(JDK_INSTALL_FILE, os.F_OK)):
      general.shell_run("./" + JDK_INSTALL_FILE,
      events={
        "ename: ": "A\r\n",
        "Press Enter to continue.....": "\r\n\r\n",
        "timeout":"-1"
      })
    else:
      raise Exception("Not able to download " + JDK_INSTALL_FILE)

def _install_glassfish():
  '''
  Installation of the glassfish application server.

  '''
  if (not os.access(GLASSFISH_PATH + "/glassfish", os.F_OK)):
    os.chdir(app.INSTALL_DIR)
    if (not os.access(GLASSFISH_INSTALL_FILE, os.F_OK)):
      general.download_file(GLASSFISH_REPO_URL, user="glassfish")

    # Create installation dir
    if (not os.access(GLASSFISH_PATH, os.F_OK)):
      os.mkdir(GLASSFISH_PATH)
      os.chmod(GLASSFISH_PATH, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)
      os.chown(GLASSFISH_PATH, 150, 550)

    # Set executeion permissions and run the installation.
    if ".zip" in GLASSFISH_INSTALL_FILE:
      general.shell_exec("unzip " + GLASSFISH_INSTALL_FILE + " -d " + GLASSFISH_PATH, user="glassfish")
      general.shell_exec("mv " + GLASSFISH_PATH + "glassfishv3/* " + GLASSFISH_PATH + "glassfishv3/.* " + GLASSFISH_PATH, user="glassfish")
    else:
      os.chmod(GLASSFISH_INSTALL_FILE, stat.S_IXUSR | stat.S_IRUSR)
      shutil.copy(app.SYCO_PATH + "var/glassfish/" + GLASSFISH_VERSION + "-unix-answer", app.INSTALL_DIR + GLASSFISH_VERSION + "-unix-answer")
      general.shell_exec("./" + GLASSFISH_INSTALL_FILE + " -a " + GLASSFISH_VERSION + "-unix-answer -s", user="glassfish")

    # Install the start script
    if (not os.access("/etc/init.d/" + GLASSFISH_VERSION, os.F_OK)):
      shutil.copy(app.SYCO_PATH + "var/glassfish/" + GLASSFISH_VERSION, "/etc/init.d/" + GLASSFISH_VERSION)
      general.shell_exec("chmod 0755 " + "/etc/init.d/" + GLASSFISH_VERSION)
      general.shell_exec("chkconfig --add " + GLASSFISH_VERSION)
      general.shell_exec("chkconfig --level 3 " + GLASSFISH_VERSION + " on")

      general.set_config_property("/etc/init.d/" + GLASSFISH_VERSION, "\$\{MYSQL_PRIMARY\}", app.get_mysql_primary_master ())
      general.set_config_property("/etc/init.d/" + GLASSFISH_VERSION, "\$\{MYSQL_SECONDARY\}", app.get_mysql_secondary_master())

  if (not os.access(GLASSFISH_DOMAINS_PATH + "domain1/config/domain.xml", os.F_OK)):
    raise Exception("Failed to install " + GLASSFISH_PATH)

  if (not os.access("/etc/init.d/" + GLASSFISH_VERSION, os.F_OK)):
    raise Exception("Failed to install /etc/init.d/" + GLASSFISH_VERSION)

def _install_eclipselink():
  '''
  http://www.eclipse.org/eclipselink
  http://wiki.eclipse.org/EclipseLink/Examples/JPA/GlassFishV3_Web_Tutorial
  http://blogs.sun.com/GlassFishPersistence/entry/updating_eclipselink_bundles_in_glassfish

  '''
  general.create_install_dir()
  os.chdir(app.INSTALL_DIR)
  if (not os.access("eclipselink-plugins-2.1.2.v20101206-r8635.zip", os.F_OK)):
    general.download_file("http://ftp.ing.umu.se/mirror/eclipse/rt/eclipselink/releases/2.1.2/eclipselink-plugins-2.1.2.v20101206-r8635.zip", user="glassfish")
    general.download_file("http://www.eclipse.org/downloads/sums.php?file=/rt/eclipselink/releases/2.1.2/eclipselink-plugins-2.1.2.v20101206-r8635.zip&type=sha1",
      "eclipselink-plugins-2.1.2.v20101206-r8635.zip.sha1",
      user="glassfish"
    )
    sha1sum = general.shell_exec("sha1sum --check eclipselink-plugins-2.1.2.v20101206-r8635.zip.sha1", user="glassfish")
    if (r"eclipselink-plugins-2.1.2.v20101206-r8635.zip: OK" not in sha1sum):
      raise Exception("Invalid checksum for eclipselink")

  general.shell_exec("unzip -oq eclipselink-plugins-2.1.2.v20101206-r8635.zip")

  general.shell_exec("cp org.eclipse.persistence.antlr_2.1.2.v20101206-r8635.jar " + GLASSFISH_PATH + "glassfish/modules/org.eclipse.persistence.antlr.jar", user="glassfish")
  general.shell_exec("cp org.eclipse.persistence.jpa_2.1.2.v20101206-r8635.jar " + GLASSFISH_PATH + "glassfish/modules/org.eclipse.persistence.jpa.jar", user="glassfish")
  general.shell_exec("cp org.eclipse.persistence.asm_2.1.2.v20101206-r8635.jar " + GLASSFISH_PATH + "glassfish/modules/org.eclipse.persistence.asm.jar", user="glassfish")
  general.shell_exec("cp org.eclipse.persistence.jpa.modelgen_2.1.2.v20101206-r8635.jar " + GLASSFISH_PATH + "glassfish/modules/org.eclipse.persistence.jpa.modelgen.jar", user="glassfish")
  general.shell_exec("cp org.eclipse.persistence.core_2.1.2.v20101206-r8635.jar " + GLASSFISH_PATH + "glassfish/modules/org.eclipse.persistence.core.jar", user="glassfish")
  general.shell_exec("cp org.eclipse.persistence.oracle_2.1.2.v20101206-r8635.jar " + GLASSFISH_PATH + "glassfish/modules/org.eclipse.persistence.oracle.jar", user="glassfish")
  general.shell_exec("cp javax.persistence_2.0.1.v201006031150.jar " + GLASSFISH_PATH + "glassfish/modules/javax.persistence.jar", user="glassfish")

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
      "Enter Current Master Password> ": "changeit\n",
      "Enter New_Master_Password password> ": app.get_glassfish_master_password() + "\n",
      "Enter New_Master_Password password again> ": app.get_glassfish_master_password() + "\n"
  }
  )

  # Create new cert for https
  # TODO move the fareoffice info to install.cfg
  os.chdir(GLASSFISH_DOMAINS_PATH + domain_name + "/config/")
  general.shell_exec("keytool -delete -alias s1as -keystore keystore.jks -storepass " + app.get_glassfish_master_password(), user="glassfish")
  general.shell_exec('keytool -keysize 2048 -genkey -alias s1as -keyalg RSA -dname "CN=Fareoffice,O=Fareoffice,L=Stockholm,S=Stockholm,C=Sweden" -validity 3650 -keypass ' + app.get_glassfish_master_password() + ' -keystore keystore.jks -storepass ' + app.get_glassfish_master_password(), user="glassfish")
  general.shell_exec("keytool -list -keystore keystore.jks -storepass " + app.get_glassfish_master_password(), user="glassfish")

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
  http://www.mysql.com/downloads/connector/j/

  '''
  os.chdir(app.INSTALL_DIR)

  if (not os.access(MYSQL_CONNECTOR_FILE, os.F_OK)):
      general.download_file(MYSQL_CONNECTOR_REPO_URL, user="glassfish")
      general.download_file(MYSQL_CONNECTOR_REPO_URL + ".asc", user="glassfish")

  general.shell_exec("gpg --keyserver keyserver.ubuntu.com --recv-keys 5072E1F5", user="glassfish")
  signature = general.shell_exec("gpg --verify " + MYSQL_CONNECTOR_FILE + ".asc", user="glassfish")
  if (r'Good signature from "MySQL Package signing key (www.mysql.com) <build@mysql.com>"' not in signature):
    raise Exception("Invalid signature.")

  # TODO: Should it be under /ext/.
  general.shell_exec("tar zxf " + MYSQL_CONNECTOR_FILE, user="glassfish")
  general.shell_exec("cp " + MYSQL_CONNECTOR_VERSION +"/" + MYSQL_CONNECTOR_VERSION + "-bin.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")

def _install_google_guice(domain_name):
  '''
  http://code.google.com/p/google-guice/
  http://code.google.com/p/google-guice/downloads/list

  '''
  os.chdir(app.INSTALL_DIR)
  if (not os.access("guice-3.0.zip", os.F_OK)):
    general.download_file("http://google-guice.googlecode.com/files/guice-3.0.zip", user="glassfish")
    general.shell_exec("unzip -oq guice-3.0.zip", user="glassfish")

  general.shell_exec("cp guice-3.0/guice-3.0.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")
  general.shell_exec("cp guice-3.0/guice-assistedinject-3.0.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")
  general.shell_exec("cp guice-3.0/aopalliance.jar " + GLASSFISH_DOMAINS_PATH + domain_name + "/lib/ext/", user="glassfish")

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
  #      no registration tree node, no Registartion in common task.
  #    * GlassFish News will not be shown in the tree node nor the common
  #      task page
  #    * The information frame under Common Task page will not be rendered.
  #
  asadmin_exec("create-jvm-options -Dcom.sun.enterprise.tools.admingui.NO_NETWORK=true", admin_port)

def _update_glassfish():
  '''
  Update the installed glassfish

  More info
  http://docs.sun.com/app/docs/doc/821-1751/ghapp?l=en&a=view

  '''
  # pkg refresh must be in a writeable dir.
  os.chdir("/tmp")

  general.shell_exec("yum -y install libidn")
  general.shell_run(GLASSFISH_PATH + "bin/pkg refresh --full",
    user="glassfish",
    events={
      re.compile('Would you like to install this software now.*'): "y\r\n"
    }
  )
  general.shell_exec("chcon -f -t textrel_shlib_t " + GLASSFISH_PATH + "pkg/vendor-packages/OpenSSL/crypto.so")

  # Need to run a second time, in the first run the pkg software might
  # have been installed, and after that the chcon needs to be executed
  # and after that the real pkg refresh needs to be executed
  general.shell_run(GLASSFISH_PATH + "bin/pkg refresh --full",
    user="glassfish",
    events={
      re.compile('Would you like to install this software now.*'): "y\r\n"
    }
  )

  general.shell_exec("/etc/init.d/" + GLASSFISH_VERSION + " stop")
  general.shell_exec(GLASSFISH_PATH + "bin/pkg image-update", user="glassfish")
  general.shell_exec("/etc/init.d/" + GLASSFISH_VERSION + " start")

def _set_iptables():
  pass