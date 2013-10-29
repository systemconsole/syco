#!/usr/bin/env python
'''
Installation procedures for the data-centers at Availo and Telecity Skondal.

- Icinga is a fork the Nagios poller which features a nicer web-interface, and some incremental functionality.
- Icinga new web is the "bells and whistles" front end to icinga.
- Ido2db/idoutils is used as an abstraction-layer between icinga and the sql-database

- PNP4Nagios handles graphing of Nagios/Icinga performance data and is integrated with the icinga web interface.
  NPCD parses performance data from icinga to PNP4Nagios.


'''

import re
import os
import string

from general import generate_password, get_install_dir, x
from installMysql import install_mysql, mysql_exec
from installNrpe import install_nrpe, list_plugin_files
import app
import config
import constant
import general
import install
import iptables
import mysqlUtils
import net
import scopen
import version


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


def install_icinga(args):
    '''
    Installs the icinga poller and web-interface.

    '''
    app.print_verbose("Installing icinga")
    version_obj = version.Version("installIcinga", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_icinga(args)
    version_obj.mark_executed()


def reload_icinga(args):
    '''
    Probes the network for new services and updates the Icinga object structure.

    '''
    # No verson checking since its not an install/uninstall
    app.print_verbose("Reloading icinga")
    _reload_icinga(args)


def _install_icinga(args):
    '''
    The icinga-installation is divided into three parts - icinga core, icinga web and PNP4Nagios. Icinga core insatlls the icinga-poller (baically
    an exakt for of the Nagios poller except with SQL integration). Icinga-core also includes a very simple GUI that is kept as a backup
    in case the fancier GUI goes down for any reason. Icinga-web is the "bells and whistles" GUI which is heavier, with "improved" looks
    and more functionality.

    '''
    # Initialize all used passwords.
    app.init_mysql_passwords()
    app.get_ldap_sssd_password()

    # Install icinga poller, web-interface and graping.
    icinga_db_password = _install_icinga_core(args)
    _install_icinga_web(icinga_db_password)
    _install_pnp4nagios()

    # Install a http index
    _install_http_index()

    # Enable SELinux
    _install_SELinux()

    # Restart all services
    x("service ido2db restart")
    x("service nrpe restart")
    x("service icinga restart")
    x("service httpd restart")


def _install_icinga_core(args):
    """
    Core installation is decently straightforward. Icinga-bins are downloaded from the EPEL-repo and and SQL-db is created
    and set up with the standard icinga db-schema.

    The "hard" part is setting up the object base, which is done in via helper functions.

    """
    # Disable SELinux for now, Install icinga-packages.
    x("setenforce 0")
    install.rforge_repo()
    x("yum -y install icinga icinga-idoutils-libdbi-mysql nagios-plugins-all nagios-plugins-nrpe")

    # Set set up icinga mysql-database
    icinga_sql_password = _setup_icinga_mysql()

    # Let ido2db know password has changed
    general.use_original_file("/etc/icinga/ido2db.cfg")
    general.set_config_property("/etc/icinga/ido2db.cfg","db_pass=icinga","db_pass={0}".format(icinga_sql_password, False))
    x("cp --remove-destination {0}syco-private/var/nagios/icinga.cfg /etc/icinga/icinga.cfg".format(constant.SYCO_USR_PATH))
    x("chown icinga:icinga /etc/icinga/icinga.cfg")

    # Add icinga-server iptables chain
    iptables.add_icinga_chain()
    iptables.save()

    # Reload the icinga object structure
    _reload_icinga(args,reload=False)

    return icinga_sql_password


def _install_icinga_web(icinga_db_pass):
    """
    This installs the icinga web module. Only source of complexity is moking icinga accessible from the document root.

    """
    x("yum install -y icinga-web php php-cli php-pear php-xmlrpc php-xsl php-pdo php-soap php-gd php-ldap php-mysql")

    # Setup icinga-web mysql
    icinga_web_db_bass = _setup_icinga_web_mysql()

    # Configure icinga web client config files
    _configure_icinga_web(icinga_db_pass, icinga_web_db_bass)

    # Allow icinga-web to issue icinga commands
    x("useradd -G icingacmd apache")

    # Make everything startup on reboot
    x("/sbin/chkconfig --level 3 httpd on")
    x("/sbin/chkconfig --level 3 mysqld on")
    x("/sbin/chkconfig --level 3 ido2db on")

    # Harden with iptables-chain
    iptables.add_httpd_chain()
    iptables.save()


def _configure_icinga_web(icinga_db_pass, web_sqlpassword):
    '''
    Sets configuration parameters for icinga-web, including MySQL-password, LDAP user-auth and timezone.

    Watch out: The repoforge package creates an icinga-web folder in /etc/ with a few XML-files, which are then linked into the
    /usr/share/icinga-web/app/config xmls through overwrite-tags. However, the icinga-web documentation assumes you are using the
    standard configs, meaning that its easier to debug/powergoodgle if not loading the includes (by just not setting apache
    permissions).

    '''
    # Configure upp database passwords
    general.use_original_file("/usr/share/icinga-web/app/config/databases.xml")
    general.set_config_property(
        "/usr/share/icinga-web/app/config/databases.xml",
        "mysql://icinga_web:icinga_web",
        "mysql://icinga-web:{0}".format(web_sqlpassword),
        False
    )
    general.set_config_property(
        "/usr/share/icinga-web/app/config/databases.xml",
        "mysql://icinga:icinga",
        "mysql://icinga:{0}".format(icinga_db_pass),
        False
    )

    # Configure LDAP login
    general.use_original_file("/etc/httpd/conf.d/icinga-web.conf ")
    x("rm -f /etc/httpd/conf.d/icinga-web.conf ")
    x("cp -p {0}icinga/icinga-web.conf /etc/httpd/conf.d/".format(constant.SYCO_VAR_PATH))
    htconf = scopen.scOpen("/etc/httpd/conf.d/icinga-web.conf ")
    htconf.replace("${BIND_DN}","cn=sssd,%s" % config.general.get_ldap_dn() )
    htconf.replace("${BIND_PASSWORD}","%s" % app.get_ldap_sssd_password() )
    htconf.replace("${LDAP_URL}","ldaps://%s:636/%s?uid" % (config.general.get_ldap_hostname(),config.general.get_ldap_dn()) )
    x("/usr/bin/icinga-web-clearcache")

    # Configure timezone and laguage
    general.use_original_file("/usr/share/icinga-web/app/config/translation.xml")
    general.set_config_property("/usr/share/icinga-web/app/config/translation.xml", "default_locale=\"en\"","default_locale=\"en\" default_timezone=\"CET\"",False)


def _reload_icinga(args, reload=True):
    '''
    Re-probes the network for running services and updates the icinga object structure.

    '''
    # Initialize all used passwords.
    app.init_mysql_passwords()
    app.get_ldap_sssd_password()

    hostList = _get_host_list()
    _append_services_to_hostlist(hostList)
    _build_icinga_config(hostList)
    _install_server_plugins()

    if reload:
        x("service icinga reload")


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
    x("chown icinga:icinga /etc/pnp4nagios/npcd.cfg")

    # Package-maker does create a log for process-perfdata. PBP goes bonkers if it can't find it
    x("touch /var/log/pnp4nagios/perfdata.log")

    # Since we are using icinga (not nagios) we need to change permissions.
    # Tried just adding icinga to nagios group but creates a dependency on PNP/Nagios package states which is not good.
    x("chown -R icinga:icinga /var/log/pnp4nagios")
    x("chown -R icinga:icinga /var/spool/pnp4nagios")
    x("chown -R icinga:icinga /var/lib/pnp4nagios")

    # Set npcd (bulk parser/spooler) to auto-start
    x(" /sbin/chkconfig --level 3 npcd on")

    # Setup LDAP-login for PNP4NAgios.
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


def _build_icinga_config(hostList):
    """
    Moves a customized icinga object configuration tree. Extends it with a hostlist according to indata hostList. Object tree
    can be extended in incremental syco plugins.

    """
    # Move the object structure and set let icinga:icingacmd read it.
    x("rm -rf /etc/icinga/objects/*")
    object_path_list = list_plugin_files("/var/nagios/objects")
    for path in object_path_list:
        x("cp -r {0}/ /etc/icinga/".format(path))
    x("chown -R icinga:icinga /etc/icinga/objects")
    x("chmod -R 750 /etc/icinga/objects")

    # Open the host-list file, and append all hosts in the hostList data-structure.
    FILE = scopen.scOpen("/etc/icinga/objects/hosts/host_list.cfg")
    for host in hostList:
        groups = host.services
        # Add the host-type as a host-group (i.e switches belongs the the "switch") hostgroup.
        groups.append(host.type)
        hostgroups = ",".join(str(x) for x in groups)
        FILE.add("define host{\nhost_name  " + host.name + "\nalias " + host.name + "\naddress " + host.ip + "\nuse " + host.type +"\nhostgroups " + hostgroups + "\n}\n\n")


def _append_services_to_hostlist(hostList):
    """
    Since the install.cfg is read-only, this function uses NRPE to poll a get_services plugin on every host. The purpose of this function
    is to figure out what host is running what services (eg apache or named)

    """
    # Cycle through the lost of hosts and add query for running servives via NRPE. Skip switches (no NRPE)
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
    # Create a list of host-objects from the syco-config (see host class)
    serverList=[]
    for server in config.get_devices():
        if config.host(server).is_guest():
            serverList.append(host(server, config.host(server).get_any_ip(), "guest"))
        elif config.host(server).is_host():
            serverList.append(host(server, config.host(server).get_any_ip(), "host"))
        elif config.host(server).is_firewall():
            serverList.append(host(server, config.host(server).get_back_ip(), "firewall"))
        elif config.host(server).is_switch():
            serverList.append(host(server, config.host(server).get_any_ip(), "switch"))
    return serverList


def _get_icinga_version():
    '''
    Checks what package version of icinga is installed (package version comes after "-" i)

    '''
    # Since repoforge may be updated, check insalled version of icinga.
    icingaversion = x("yum list installed | grep icinga.x86_64").split()[1].split("-")[0]
    app.print_verbose(icingaversion)
    return icingaversion

def _get_icinga_web_version():
    '''
    Checks what package version of icinga is installed (package version comes after "-" i)

    '''
    # Since repoforge may be updated, check insalled version of icinga.
    icingaversion = x("yum list installed | grep icinga-web.noarch").split()[1].split("-")[0]
    app.print_verbose(icingaversion)
    return icingaversion


def _install_http_index():
    '''
    Moves a static http index file to the apache root directory. TODO: HttpdUtils function.

    '''
    x("cp /opt/syco/var/icinga/index.html /var/www/html/index.html")
    x("chown apache:apache /var/www/html/index.html")


def _install_server_plugins():
    '''
    Install plugins that are executed on the icinga-server (SNMP queries to switch etc)

    '''
    _install_server_plugins_dependencies()

    # These install snmp plugins
    snmp_plugin_path = "{0}lib/nagios/plugins_snmp/".format(app.SYCO_PATH)
    nagios_plugin_path = "/usr/lib64/nagios/plugins/"
    for plugin in os.listdir(snmp_plugin_path):
        x("cp {0}{2} {1}{2}".format(snmp_plugin_path,nagios_plugin_path,plugin))
        x("chown icinga:nrpe {0}{1}".format(nagios_plugin_path,plugin))
        x("chmod ug+x {0}{1}".format(nagios_plugin_path,plugin))

    # Set switch password for SNMP switch plugins
    switch_check_file = scopen.scOpen("/etc/icinga/objects/commands/specific_checks.cfg")
    switchpass = app.get_switch_icmp_password().replace("&","\&").replace("/","\/")
    switch_check_file.replace("$(SWITCHPASS)", switchpass)

    #x("chown -R icinga:icingacmd /usr/lib64/nagios/plugins")
    x("usermod -a -G nrpe icinga")


def _install_server_plugins_dependencies():
    '''
    Install libraries/binaries that the server plugins depend on.

    '''
    # Dependency for check_switch_mac_table
    x("yum install -y net-snmp-utils")


def _setup_icinga_mysql():
    '''
    Set up a mysql database for icinga

    '''
    # Create and configure. Install hardened MySQL if needed.
    if not os.path.exists('/etc/init.d/mysqld'):
        install_mysql(["","1","1G"])
    sqlpassword = generate_password(40,chars=string.letters+string.digits)

    # Create MySQL icinga user
    mysqlUtils.drop_user('icinga')
    mysqlUtils.create_user('icinga', sqlpassword, 'icinga')

    # Create MySQL database schema for icinga.
    x("mysql --user='{0}' --password='{1}' -e 'CREATE DATABASE icinga'".format("icinga",re.escape(sqlpassword)))
    x("mysql icinga --user='{0}' --password='{1}' < /usr/share/doc/icinga-idoutils-libdbi-mysql-{2}/db/mysql/mysql.sql".format("icinga",re.escape(sqlpassword), _get_icinga_version()))

    return sqlpassword


def _setup_icinga_web_mysql():
    '''
    Set up a mysql database for icinga-web

    '''
    # Generate a random password and add the icinga_web user
    web_sqlpassword = generate_password(40, chars=string.letters+string.digits)
    mysqlUtils.create_user('icinga-web', web_sqlpassword, 'icinga_web')

    # Build database tables from supplied schema
    x("mysql --user='{0}' --password='{1}' -e 'CREATE DATABASE icinga_web'".format("icinga-web",re.escape(web_sqlpassword)))
    x("mysql icinga_web  --user='{0}' --password='{1}' < /usr/share/doc/icinga-web-{2}/schema/mysql.sql".format("icinga-web",re.escape(web_sqlpassword),_get_icinga_web_version()))

    # Append a login password for "icingaadmin".
    x("mysql --user='{0}' --password='{1}' < {2}syco-private/var/nagios/{3}".format("icinga-web",re.escape(web_sqlpassword), constant.SYCO_USR_PATH,"icinga_password.sql"))

    return web_sqlpassword


def _install_SELinux():
    '''
    Install SELinux policies for Icinga, icinga-web and pnp4nagios.
    See .te files for policy details.

    '''
    # Create a local dir for SELinux modules
    x("mkdir -p /var/lib/syco_selinux_modules/server")
    module_path = "{0}var/icinga/SELinux_modules".format(app.SYCO_PATH)
    x("cp {0}/*.pp /var/lib/syco_selinux_modules/server".format(module_path))
    x("semodule -i /var/lib/syco_selinux_modules/server/*.pp")

    # Enable SELinux after successfil installation
    x("setenforce 1")


class host():
    '''
    Objcect which wrapps all host-data needed by icinga.

    '''
    def __init__(self,configname,configip,hosttype):
        self.name = configname
        self.ip = configip
        self.type = hosttype
        self.services = []

