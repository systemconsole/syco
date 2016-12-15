#!/usr/bin/env python
"""
Install glassfish with optimizations, security and common plugins.

Read more
http://www.oracle.com/technetwork/middleware/glassfish/documentation/index.html
http://glassfish.java.net/
http://www.nabisoft.com/tutorials/glassfish/installing-glassfish-301-on-ubuntu
http://iblog.humani-tech.com/?p=505

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import traceback

import app
import general
import version
import sys
import config
from scopen import scOpen
from general import x


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


# NOTE: Remember to change path in "var/glassfish/glassfish-4"
GLASSFISH_VERSION      = "glassfish-4.1"
GLASSFISH_INSTALL_FILE = GLASSFISH_VERSION + ".zip"
GLASSFISH_REPO_URL     = "http://packages.fareoffice.com/glassfish/" + GLASSFISH_INSTALL_FILE

# Icinga plugins directory
ICINGA_PLUGINS_DIR = "/usr/lib64/nagios/plugins/"

# Mysql Connector
# http://ftp.sunet.se/pub/unix/databases/relational/mysql/Downloads/Connector-J/
# http://www.mysql.com/downloads/connector/j/
MYSQL_FILE_NAME="mysql-connector-java-5.1.38"
MYSQL_CONNECTOR_REPO_URL="http://packages.fareoffice.com/mysql-connect/"+MYSQL_FILE_NAME+".tar.gz"


# Google Guice
# Is configured in _install_google_guice.
GUICE_NAME="guice-3.0"
GUICE_URL="http://packages.fareoffice.com/guice/"+GUICE_NAME+".zip"


def build_commands(commands):
    """
    Defines the commands that can be executed through the syco.py shell script.

    """
    commands.add("install-glassfish4", install_glassfish, help="Install on the current server.")


def iptables_setup():
    """Called from iptables.py

    Iptable rules are configured from applications using glassfish.
    """
    pass


def install_glassfish(arg):
    """Install glassfish4"""
    app.print_verbose("Install glassfish 4 script-version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("install-glassfish-4", SCRIPT_VERSION)
    version_obj.check_executed()

    try:
        initialize_passwords()
        general.create_install_dir()
        x("yum install unzip -y")

        if not _is_glassfish_user_installed():
            # Add a new group for glassfish administration.
            # This can be used for all users that should be able to
            # adminitrate glassfish.
            x("groupadd glassfish -g 200")

            # Give glassfish it's own user.
            x("adduser -m -r --shell /bin/bash -u200 -g200 glassfish")

        _check_java_installed()
        _install_glassfish()
        _setup_glassfish4()
        _install_mysql_connect()
        _install_guice()
        _install_icinga_ulimit_check()
        _set_domain_passwords()

        # Restart to get all options take affect.
        x("/etc/init.d/glassfish-4 stop -n")
        x("/etc/init.d/glassfish-4 start -n")

        version_obj.mark_executed()
    except Exception, error_text:
        app.print_error("Failed to install glassfish")
        app.print_error(error_text)
        traceback.print_exc(file=sys.stdout)
    finally:
        x("yum remove unzip -y")


def initialize_passwords():
    """
    Initialize all passwords that used by the script.

    This is done in the beginning of the script to prevent the script from
    stopping in the middle asking user for password.

    """
    app.get_glassfish_master_password()
    app.get_glassfish_admin_password()



def _is_glassfish_user_installed():
    """Check if glassfish user is installed."""
    for line in open("/etc/passwd"):
        if "glassfish" in line:
            return True
    return False


def _check_java_installed():
    """Installation of the java sdk."""
    if not os.access("/usr/bin/java", os.F_OK):
        raise Exception("Java is not installed on this server.")


def _install_glassfish():
    """Installation of the glassfish application server."""
    if not os.access("/usr/local/glassfish4/glassfish", os.F_OK):
        os.chdir(app.INSTALL_DIR)
        if not os.access(GLASSFISH_INSTALL_FILE, os.F_OK):
            general.download_file(GLASSFISH_REPO_URL)

        if os.access(GLASSFISH_INSTALL_FILE, os.F_OK):
            # Set execute permissions and run the installation.
            x("unzip %s -d /usr/local/" % GLASSFISH_INSTALL_FILE)
            x("chown glassfish:glassfish -R /usr/local/glassfish4")
        else:
            raise Exception("Not able to download %s" % GLASSFISH_INSTALL_FILE)

        # Install the start script
        # It's possible to do this from glassfish with "asadmin create-service",
        # but our own script is a little bit better. It creates startup log
        # files and has a better "start user" functionality.
        x("cp " + app.SYCO_PATH + "var/glassfish/glassfish-4 /etc/init.d/glassfish-4")
        x("chown root:root /etc/init.d/glassfish-4")
        x("chmod 0755 " + "/etc/init.d/glassfish-4")
        x("/sbin/chkconfig --add glassfish-4")
        x("/sbin/chkconfig --level 3 glassfish-4 on")

        scOpen("/etc/init.d/glassfish-4").replace("${MYSQL_PRIMARY}", config.general.get_mysql_primary_master_ip())
        scOpen("/etc/init.d/glassfish-4").replace("${MYSQL_SECONDARY}", config.general.get_mysql_secondary_master_ip())

        x("/etc/init.d/glassfish-4 start -n")
        x("rm -f /etc/init.d/GlassFish_domain1")

    xml="/usr/local/glassfish4/glassfish/domains/domain1/config/domain.xml"
    if not os.access(xml, os.F_OK):
        raise Exception("Failed to install ")

    if (not os.access("/etc/init.d/glassfish-4", os.F_OK)):
        raise Exception("Failed to install /etc/init.d/glassfish-4")


def _setup_glassfish4():
    """Setting Glassfish 4 properties"""
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

    # Change product name to hide server information
    asadmin_exec("create-jvm-options -Dproduct.name=warpspeed")

    # Setting monitors levels
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.connector-connection-pool=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.connector-service=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.ejb-container=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.http-service=LOW")
    # asadmin_exec("set server.monitoring-service.module-monitoring-levels.sip-service=LOW")#not available
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.jdbc-connection-pool=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.jms-service=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.jvm=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.orb=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.thread-pool=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.transaction-service=LOW")
    asadmin_exec("set server.monitoring-service.module-monitoring-levels.web-container=LOW")

    # Set JMX settings
    # TODO: Remove on production
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

    # Increase thread pool sizes
    asadmin_exec("set server.thread-pools.thread-pool.http-thread-pool.max-thread-pool-size=200")
    asadmin_exec("set server.thread-pools.thread-pool.http-thread-pool.min-thread-pool-size=50")
    asadmin_exec("set server.thread-pools.thread-pool.http-thread-pool.max-queue-size=2048")
    asadmin_exec("set server.thread-pools.thread-pool.thread-pool-1.max-thread-pool-size=200")
    asadmin_exec("set server.thread-pools.thread-pool.thread-pool-1.min-thread-pool-size=50")
    asadmin_exec("set server.thread-pools.thread-pool.thread-pool-1.max-queue-size=2048")

    # Increase http acceptor threads, recomended is same as number of cpu cores.
    # Needs to be tested more together with ulimit settings before implementation.
    # asadmin_exec("set server-config.network-config.transports.transport.tcp.acceptor-threads=4")

    # Remove x-powered by to hide server information
    asadmin_exec("set server-config.network-config.protocols.protocol.http-listener-1.http.xpowered-by=false")
    asadmin_exec("set server-config.network-config.protocols.protocol.http-listener-2.http.xpowered-by=false")


def _install_mysql_connect():
    """Install the mysql connect"""
    os.chdir(app.INSTALL_DIR)
    general.download_file(MYSQL_CONNECTOR_REPO_URL)
    x("tar -zxvf "+MYSQL_FILE_NAME+".tar.gz")
    x("\cp -f "+MYSQL_FILE_NAME+"/"+MYSQL_FILE_NAME+"-bin.jar /usr/local/glassfish4/glassfish/domains/domain1/lib/ext/")
    x("chown glassfish:glassfish -R /usr/local/glassfish4/glassfish/domains/domain1/lib/ext/*")


def _install_guice():
    """Installing guice to glassfish"""
    os.chdir(app.INSTALL_DIR)
    general.download_file(GUICE_URL)
    x("unzip -o "+GUICE_NAME+".zip")
    x("cp "+GUICE_NAME+ "/" +GUICE_NAME+ ".jar /usr/local/glassfish4/glassfish/domains/domain1/lib/ext/")
    x("cp "+GUICE_NAME+ "/guice-assistedinject* /usr/local/glassfish4/glassfish/domains/domain1/lib/ext/")
    x("cp "+GUICE_NAME+ "/aopalliance* /usr/local/glassfish4/glassfish/domains/domain1/lib/ext/")
    x("cp "+GUICE_NAME+ "/javax.inject* /usr/local/glassfish4/glassfish/domains/domain1/lib/ext/")
    x("chown glassfish:glassfish -R /usr/local/glassfish4/glassfish/domains/domain1/lib/ext/*")


def _set_domain_passwords():
    """Security configuration"""
    asadmin_exec("stop-domain")

    # Change master password, default=empty
    asadmin_exec(
        "change-master-password --savemasterpassword=true ",
        admin_port=None,
        events={
            "(?i)Enter the current master password.*": "changeit\n",
            "(?i)Enter the new master password.*": app.get_glassfish_master_password() + "\n",
            "(?i)Enter the new master password again.*": app.get_glassfish_master_password() + "\n"
        }
    )
#The following custom cert creation didnt work, causing internal server error when login to glassfish. javax.net.ssl.SSLHandshakeException:
# sun.security.validator.ValidatorException: PKIX path building failed: sun.security.provider.certpath.SunCertPathBuilderException:
# unable to find valid certification path to requested target
    # Create new cert for https
#    os.chdir("/usr/local/glassfish4/glassfish/domains/domain1/config/")
#    x("keytool -delete -alias s1as -keystore keystore.jks -storepass '" + app.get_glassfish_master_password() + "'", user="glassfish")
#    x(
#        'keytool -keysize 2048 -genkey -alias s1as -keyalg RSA -dname "' +
#        'CN=' + config.general.get_organization_name() +
#        ',O=' + config.general.get_organization_name() +
#        ',L=' + config.general.get_locality() +
#        ',S=' + config.general.get_state() +
#        ',C=' + config.general.get_country_name() +
#        '" -validity 3650' +
#        " -keypass '" + app.get_glassfish_master_password() + "'" +
#        ' -keystore keystore.jks' +
#        " -storepass '" + app.get_glassfish_master_password() + "'",
#        user="glassfish"
#    )

    #
    x("keytool -delete -alias gtecybertrust5ca -keystore cacerts.jks -storepass '" + app.get_glassfish_master_password() +"'")

    asadmin_exec("start-domain ")

    # Change admin password
    asadmin_exec(
        "change-admin-password",
        admin_port=None,
        events={
            "(?i)Enter admin user name.*": "admin\n",
            "(?i)Enter the admin password.*": "\n",
            "(?i)Enter the new admin password.*": app.get_glassfish_admin_password() + "\n",
            "(?i)Enter the new admin password again.*": app.get_glassfish_admin_password() + "\n"
        }
    )

    # Stores login info for glassfish user in /home/glassfish/.asadminpass
    asadmin_exec(
        "login",
        events={
            "Enter admin user name.*": "admin\n",
            "Enter admin password.*": app.get_glassfish_admin_password() + "\n"
        }
    )

    # Enabling admin on port 4848 from external ip
    asadmin_exec(
        " --host 127.0.0.1 --port 4848 enable-secure-admin",
        events={
            "Enter admin user name.*": "admin\n",
            "Enter admin password.*": app.get_glassfish_admin_password() + "\n"
        }
    )
    asadmin_exec("stop-domain ")
    asadmin_exec("start-domain ")


def _install_icinga_ulimit_check():
    """
    If icinga is configured to check this server with check_ulimit_glassfish it
    will now get current status.

    """
    nrpe_sudo_path = "/etc/sudoers.d/nrpe"
    common_cfg_path = "/etc/nagios/nrpe.d/common.cfg"
    icinga_script = "check_ulimit.py"

    # Does the checkscript already exist? Otherwise copy it in place.
    if False == os.path.isfile("{0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script)):
        x("cp {0}lib/nagios/plugins_nrpe/{2} {1}{2}".format(app.SYCO_PATH, ICINGA_PLUGINS_DIR, icinga_script))

    # Set permissions and SELinux rules to the checkscript. Can be runned
    # multiple times without problem.
    x("chmod 755 {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script))
    x("chown nrpe:nrpe {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script))
    x("chcon -t nagios_unconfined_plugin_exec_t {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script))
    x("semanage fcontext -a -t nagios_unconfined_plugin_exec_t {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script))

    # Add lines to sudoers, common.cfg if they dont already exist. Can only be
    # runned once.
    nrpe_string_1 = "nrpe ALL=NOPASSWD: {0}{1}".format(ICINGA_PLUGINS_DIR, icinga_script)
    nrpe_string_2 = "command[check_ulimit_glassfish]=sudo {0}check_ulimit.py glassfish 60 80".format(ICINGA_PLUGINS_DIR)

    sudoers_nrpe = open(nrpe_sudo_path, "r+")
    if sudoers_nrpe.read().find(nrpe_string_1) == -1:
        x("echo \"{0}\" >> {1}".format(nrpe_string_1, nrpe_sudo_path))
    sudoers_nrpe.close()

    common_cfg = open(common_cfg_path, "r+")
    if common_cfg.read().find(nrpe_string_2) == -1:
        x("echo \"{0}\" >> {1}".format(nrpe_string_2, common_cfg_path))
    common_cfg.close()

    # Finally restart the nrpe service to load the new check.
    x("service nrpe restart")


def asadmin_exec(command, admin_port=None, events=None):
    if admin_port:
        cmd = "/usr/local/glassfish4/bin/asadmin --port " + admin_port + " " + command
    else:
        cmd = "/usr/local/glassfish4/bin/asadmin --echo " + command

    if events:
        return general.shell_run(cmd, user="glassfish", events=events)
    else:
        return x(cmd, user="glassfish")
