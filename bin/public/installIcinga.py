#!/usr/bin/env python
'''
Installation procedures for the data-centers at Availo and Telecity Skondal.

Icinga is a fork of nagios which features a nicer web-interface, and some incremental functionality.
Icinga new web is the "bells and whistles" front end to icinga.
Ido2db/idoutils is used as an abstraction-layer between icinga and the sql-database
NPCD parses performance data from icinga (found in tmp, and spools it into a smart format, and hands it to PNP4Nagios)
PNP4Nagios handles graphing of Nagios/Icinga performance data and is integrated with the icinga web interface.


'''

import app
import config
import constant
import general
from general import generate_password, get_install_dir, x
import re
import os
import iptables
import install
import version
import mysqlUtils
from installMysql import install_mysql, mysql_exec
import string
import scopen


__author__ = "elis.kullberg@netlight.com"
__copyright__ = "Copyright 2012, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Elis Kullberg"
__email__ = "above"
__credits__ = ["Daniel & Mattias"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Development"

SCRIPT_VERSION = 1


def build_commands(commands):
    commands.add("install-icinga", install_icinga, help="Installs a icinga poller and web-interface for monitoring of remote hosts.")
    commands.add("reload-icinga", reload_icinga, help="Reloads the icinga object structure.")
    commands.add("install-nrpe", install_nrpe, help="Installs NRPE daemon and nagios plugins for monitoring by remote server.")

def install_icinga(args):
    '''
    Installs the icinga poller and web-interface
    '''
    app.print_verbose("Installing icinga")
    version_obj = version.Version("installIcinga", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_icinga(args)
    version_obj.mark_executed()

def reload_icinga(args):
    '''
    This function probes the network for new services and updates the object structure Icinga uses to know what to to monitor and how.
    '''
    # No verson checking since its not an install/uninstall
    app.print_verbose("Reloading icinga")
    _reload_icinga(args)

def install_nrpe(args):
    '''
    This function installs an NRPE server (to be run on every host), plugins and commands. It also hardens the server.
    '''
    app.print_verbose("Installing nrpe")
    version_obj = version.Version("installNrpe", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_nrpe(args)
    version_obj.mark_executed()


def _append_services(hostList):
    """
    Since the install.cfg is read-only, this function uses NRPE to poll a get_services plugin on every host. The purpose of this function
    is to figure out what host is running what services (eg apache or named)
    """
    for host in hostList:
        if host.type != "switch":
            nrpe_return = x("/usr/lib64/nagios/plugins/check_nrpe -H " + host.ip + " -c get_services").split()
            if (nrpe_return.pop(0) == "OK"):
                host.services = nrpe_return
            else:
                app.print_verbose(host.name + " is not running NRPE, omitted")
    return hostList

def _get_host_list():
    """
    This function polls through all hosts in the /opt/syco/etc/install.cfg and sorts them into host types (see object model UML).
    A host class is defined in the bottom of this script. Host objects are instantiated with hostname, front-ip, and type in this function.
    """
    serverList=[]
    for server in config.get_servers():
        if config.host(server).is_guest():
            serverList.append(host(server, config.host(server).get_any_ip(),"guest"))
        elif config.host(server).is_host():
            serverList.append(host(server, config.host(server).get_any_ip(),"host"))
        elif config.host(server).is_firewall():
            serverList.append(host(server, config.host(server).get_any_ip(),"firewall"))
        elif config.host(server).is_switch():
            serverList.append(host(server, config.host(server).get_any_ip(),"switch"))
    return serverList

def _get_icinga_version():
    ''' Checks what package version of icinga is installed (package version comes after "-" i) '''
    icingaversion = x("yum list installed | grep icinga.x").split()[1].split("-")[0]
    app.print_verbose(icingaversion)
    return icingaversion


def _install_icinga_core(args):
    """
    Core installation is decently straightforward. Icinga-bins are downloaded from the EPEL-repo and and SQL-db is created
    and set up with the standard icinga db-schema.

    The "hard" part is setting up the object base, which is done in via helper functions.
    """
    # Disable SELinux, will mess up httpd aliases toward /usr/lib/. Done statefully later.
    x("setenforce 0")
    # Install packages
    install.rforge_repo()
    x("yum -y install icinga icinga-idoutils-libdbi-mysql nagios-plugins-all nagios-plugins-nrpe")
    # Create database with icinga user
    app.init_mysql_passwords()
    if not os.path.exists('/etc/init.d/mysqld'):
        install_mysql(["","1","1G"])
    sqlpassword = generate_password(40,chars=string.letters+string.digits)
    mysqlUtils.drop_user('icinga')
    mysqlUtils.create_user('icinga', sqlpassword, 'icinga')
    x("mysql --user='{0}' --password='{1}' -e 'CREATE DATABASE icinga'".format("icinga",re.escape(sqlpassword)))
    x("mysql icinga --user='{0}' --password='{1}' < /usr/share/doc/icinga-idoutils-libdbi-mysql-{2}/db/mysql/mysql.sql".format("icinga",re.escape(sqlpassword), _get_icinga_version()))
    # Let ido2db know password has changed
    general.use_original_file("/etc/icinga/ido2db.cfg")
    general.set_config_property("/etc/icinga/ido2db.cfg","db_pass=icinga","db_pass={0}".format(sqlpassword, False))
    x("cp -p --remove-destination {0}syco-private/var/nagios/icinga.cfg /etc/icinga/icinga.cfg".format(constant.SYCO_USR_PATH))
    # Harden with iptables
    iptables.add_monitor_chain()
    # Monitor needs to be able to check itself!
    install_nrpe(args)
    # Configure object structure
    hostList = _get_host_list()
    _append_services(hostList)
    _move_object_base_structure_icinga()
    _write_hosts_config_icinga(hostList)
    # Install SNMP plugins
    _install_server_plugins()
    return sqlpassword

def _reload_icinga(args):
    hostList = _get_host_list()
    _append_services(hostList)
    _move_object_base_structure_icinga()
    _write_hosts_config_icinga(hostList)
    _install_server_plugins()

def _install_icinga_web(icinga_db_pass):
    """
    This installs the icinga web module. Only source of complexity is moking icinga accessible frmo the document root.
    """
    x("yum install -y icinga-web php php-cli php-pear php-xmlrpc php-xsl php-pdo php-soap php-gd php-ldap php-mysql")
    web_sqlpassword = generate_password(40,chars=string.letters+string.digits)
    mysqlUtils.create_user('icinga-web', web_sqlpassword, 'icinga_web')
    x("mysql --user='{0}' --password='{1}' -e 'CREATE DATABASE icinga_web'".format("icinga-web",re.escape(web_sqlpassword)))
    x("mysql icinga_web  --user='{0}' --password='{1}' < /usr/share/doc/icinga-web-{2}/schema/mysql.sql".format("icinga-web",re.escape(web_sqlpassword),_get_icinga_version()))
    # Append every plugin-defined passowrd to mysql-table.
    x("mysql --user='{0}' --password='{1}' < {2}syco-private/var/nagios/{3}".format("icinga-web",re.escape(web_sqlpassword), constant.SYCO_USR_PATH,"icinga_password.sql"))
    general.use_original_file("/usr/share/icinga-web/app/config/databases.xml")
    general.set_config_property("/usr/share/icinga-web/app/config/databases.xml","mysql://icinga_web:icinga_web","mysql://icinga-web:{0}".format(web_sqlpassword), False)
    general.set_config_property("/usr/share/icinga-web/app/config/databases.xml","mysql://icinga:icinga","mysql://icinga:{0}".format(icinga_db_pass), False)
    # Allow icinga-web to issue icinga commands
    x("useradd -G icingacmd apache")
    # Clear any icinga cache that has alreaedy acumulated
    general.use_original_file("/etc/httpd/conf.d/icinga-web.conf ")
    x("rm -f /etc/httpd/conf.d/icinga-web.conf ")
    x("cp -p {0}icinga/icinga-web.conf /etc/httpd/conf.d/".format(constant.SYCO_VAR_PATH))
    htconf = scopen.scOpen("/etc/httpd/conf.d/icinga-web.conf ")
    htconf.replace("${BIND_DN}","cn=sssd,%s" % config.general.get_ldap_dn() )
    htconf.replace("${BIND_PASSWORD}","%s" % app.get_ldap_sssd_password() )
    htconf.replace("${LDAP_URL}","ldaps://%s:636/%s?uid" % (config.general.get_ldap_hostname(),config.general.get_ldap_dn()) )
    x("/usr/bin/icinga-web-clearcache")
    # Make install stateful
    general.set_config_property("/etc/sysconfig/selinux", "SELINUX=enforcing", "SELINUX=permissive")
    x("/sbin/chkconfig --level 3 httpd on")
    x("/sbin/chkconfig --level 3 mysqld on")
    x("/sbin/chkconfig --level 3 ido2db on")
    # Harden with iptables-chain
    iptables.add_httpd_chain()

def _install_icinga(args):
    '''
    The icinga-installation is divided into two parts - icinga core and icinga web. Icinga core insatlls the icinga-poller (baically
    an exakt for of the Nagios poller except with SQL integration). Icinga-core also includes a very simple GUI that is kept as a backup
    in case the fancier GUI goes down for any reason. Icinga-web is the "bells and whistles" GUI which is heavier, with "improved" looks
    and more functionality.
    '''
    icinga_db_pass = _install_icinga_core(args)
    _install_icinga_web(icinga_db_pass)
    _install_pnp4nagios()
    x("service ido2db restart")
    x("service nrpe restart")
    x("service icinga restart")
    x("service httpd restart")

def _install_nrpe(args):
    '''
    The nrpe installation is quite standard - except that the stock NRPE.conf is replaced with a prepped one. After being moved
    the prepped file also has the IP of the monitor server added, so that the server only listens to this IP. Not super safe but
    better than nothing. Also, argument parsing is _disabled_.
    '''
    install.epel_repo()
    hostList = _get_host_list()

    # Confusing that nagios-plugins-all does not really include all plugins
    x("yum install nagios-plugins-all nrpe nagios-plugins-nrpe php-ldap nagios-plugins-perl perl-Net-DNS perl-Proc-ProcessTable perl-Date-Calc -y")

    # Move object structure and prepare conf-file
    x("rm -rf /etc/nagios/nrpe.d")
    x("rm -rf /etc/nagios/nrpe.cfg")
    x("cp -r {0}syco-private/var/nagios/nrpe.d /etc/nagios/".format(constant.SYCO_USR_PATH))
    x("cp {0}syco-private/var/nagios/nrpe.cfg /etc/nagios/".format(constant.SYCO_USR_PATH))

    # Extra plugins installed
    _install_nrpe_plugins()
    app.print_verbose("Setting monitor server:" + config.general.get_monitor_server())

    # Allow only monitor to query NRPE
    general.set_config_property("/etc/nagios/nrpe.cfg", "$(MONITORIP)" ,config.general.get_monitor_server(),False)

    # Figure out what servers to query.
    x("/sbin/chkconfig --level 3 nrpe on")
    x("service nrpe restart")


def _install_server_plugins():
    _install_server_plugins_dependencies()
    # These are plugins for the Icinga-server, no need for install on hosts.
    x("chmod +x {0}lib/nagios/plugins_snmp/*".format(constant.SYCO_PATH))
    x("cp -p {0}lib/nagios/plugins_snmp/* /usr/lib64/nagios/plugins/".format(constant.SYCO_PATH))


def _install_server_plugins_dependencies():
    # Dependency for check_switch_mac_table
    x("yum install -y net-snmp-utils")


def _install_pnp4nagios():
    '''
    PNP4Nagios is design to work with Nagios - some hacking is needed to make it play nice with icinga, especially with file permissions
    creating files that the EPEL-package has missed. PNP4Nagios uses the NPCD-daemon to spool data from Icinga to Round Robin Databases. I.e
    using bulk mode, see http://docs.pnp4nagios.org/_detail/bulk.png

    '''
    # Get packages from epel repo
    install.epel_repo()
    x("yum install -y pnp4nagios icinga-web-module-pnp")
    # Pnp4 uses the nagios password file, which will not exist
    general.use_original_file("/etc/httpd/conf.d/pnp4nagios.conf")
    general.set_config_property("/etc/httpd/conf.d/pnp4nagios.conf","AuthName \"Nagios Access\"","AuthName \"Icinga Access\"", False)
    general.set_config_property("/etc/httpd/conf.d/pnp4nagios.conf","AuthUserFile /etc/nagios/passwd","AuthUserFile /etc/icinga/passwd",False)
    # NPCD config prepped to work with icinga instead of nagios
    x("cp {0}syco-private/var/nagios/npcd.cfg /etc/pnp4nagios/npcd.cfg".format(constant.SYCO_USR_PATH))
    # Package-maker forgot to create a log for process-perfdata. PBP goes bonkers if it can't find it
    x("touch /var/log/pnp4nagios/perfdata.log")
    # Since we are using icinga (not nagios) we need to change permissions.
    # Tried just adding icinga to nagios group but creates a dependency on PNP/Nagios package states which is not good.
    x("chown -R icinga:icinga /var/log/pnp4nagios")
    x("chown -R icinga:icinga /var/spool/pnp4nagios")
    x("chown -R icinga:icinga /var/lib/pnp4nagios")
    # Set npcd (bulk parser/spooler) to auto-start
    x(" /sbin/chkconfig --level 3 npcd on")
    general.use_original_file("/etc/httpd/conf.d/pnp4nagios.conf")
    x("rm -f /etc/httpd/conf.d/pnp4nagios.conf")
    x("cp -p {0}icinga/pnp4nagios.conf /etc/httpd/conf.d/".format(constant.SYCO_VAR_PATH))
    htconf = scopen.scOpen("/etc/httpd/conf.d/pnp4nagios.conf")
    htconf.replace("${BIND_DN}","cn=sssd,%s" % config.general.get_ldap_dn() )
    htconf.replace("${BIND_PASSWORD}","%s" % app.get_ldap_sssd_password() )
    htconf.replace("${LDAP_URL}","ldaps://%s:636/%s?uid" % (config.general.get_ldap_hostname(),config.general.get_ldap_dn()) )
    # Restart everything
    x("service icinga restart")
    x("service httpd restart")
    x("service npcd restart")


def _install_nrpe_plugins():
    _install_nrpe_plugins_dependencies()
    x("chmod +x {0}lib/nagios/plugins_nrpe/*".format(constant.SYCO_PATH))
    x("cp -p {0}lib/nagios/plugins_nrpe/* /usr/lib64/nagios/plugins/".format(constant.SYCO_PATH))


def _install_nrpe_plugins_dependencies():
    # Dependency for check_rsyslog
    x("yum install -y MySQL-python")

    # Dependency for check_clamav
    x("yum install -y nagios-plugins-perl perl-Net-DNS-Resolver-Programmable")

    # Dependency for check_clamscan
    x("yum install -y perl-Proc-ProcessTable perl-Date-Calc")

    # Dependency for check_ldap
    x("yum install -y php-ldap")


def _move_object_base_structure_icinga():
    """
    Clear the icinga example object fiels. Move the icinga prepped icinga base structure from syco-private to /etc/icinga/ .
    User is responsible for object definitions not overlapping for now.
    """
    x("rm -rf /etc/icinga/objects/*")
    object_path_list = list_plugin_files("/var/nagios/objects")
    for path in object_path_list:
        x("cp -r {0}/ /etc/icinga/".format(path))
    x("chown -R icinga:icinga /etc/icinga/objects")
    x("chmod -R 750 /etc/icinga/objects")


def _write_hosts_config_icinga(serverList):
    """
    We open the nagios host-config file and formatted string for every host in the serverList that has been prepped previously.
    """
    FILE = scopen.scOpen("/etc/icinga/objects/hosts/host_list.cfg")
    for host in serverList:
        groups = host.services
        groups.append(host.type)
        hostgroups = ",".join(str(x) for x in groups)
        FILE.add("define host{\nhost_name  " + host.name + "\nalias " + host.name + "\naddress " + host.ip + "\nuse " + host.type +"\nhostgroups " + hostgroups + "\n}\n\n")


def list_plugin_files(path):
    '''Returns a full file-path for every plugin with the arg-0 sub-path defined'''
    if (os.access(app.SYCO_USR_PATH, os.F_OK)):
        for plugin in os.listdir(app.SYCO_USR_PATH):
            plugin_path = os.path.abspath(app.SYCO_USR_PATH + plugin + path)
            if (os.access(plugin_path, os.F_OK)):
                yield plugin_path


class host():

    def __init__(self,configname,configip,hosttype):
        self.name = configname
        self.ip = configip
        self.type = hosttype
        self.services = []



