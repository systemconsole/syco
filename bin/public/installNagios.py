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
import general
import re
import iptables
import install
import installMysql
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
    commands.add("install-nrpe", install_nrpe, help="Installs NRPE daemon and nagios plugins for monitoring by remote server.")
    commands.add("install-pnp4nagios", install_pnp4nagios, help="Install PNP4Nagios.")


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

def install_pnp4nagios(args):
    '''
    PNP4Nagios is used to store Nagios plugin performance data in an intelligen manner, and present nice graphs that integrated
    with the Icinga GUI. 
    '''
    app.print_verbose("Installing pnp4nagios")
    version_obj = version.Version("install_pnp4nagios", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_pnp4nagios(args)
    version_obj.mark_executed() 


def _append_services(hostList):
    """
    Since the install.cfg is read-only, this function uses NRPE to poll a get_services plugin on every host. The purpose of this function
    is to figure out what host is running what services (eg apache or named)
    """
    for host in hostList:
        if host.type != "switch":    
            nrpe_return = general.x("/usr/lib64/nagios/plugins/check_nrpe -H " + host.ip + " -c get_services").split()
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
        if bool(re.search('fw', server)):
            serverList.append(host(server, config.host(server).get_front_ip(),"firewall"))
        elif  bool(re.search('vh', server)):
            serverList.append(host(server, config.host(server).get_front_ip(),"virtual_host"))
        elif bool(re.search('switch', server)): 
            serverList.append(host(server, config.host(server).get_front_ip(),"switch"))
        else : 
            serverList.append(host(server, config.host(server).get_front_ip(),"virtual_guest"))
    return serverList

def _install_icinga_core(args):
    """
    Core installation is decently straightforward. Icinga-bins are downloaded from the EPEL-repo and and SQL-db is created
    and set up with the standard icinga db-schema. 

    The "hard" part is setting up the object base, which is done in via helper functions. 
    """
    # Disable SELinux, will mess up httpd aliases toward /usr/lib/
    general.x("setenforce 0")
    install.rforge_repo()
    # Install packages
    general.x("yum -y install icinga icinga-gui icinga-doc icinga-idoutils-libdbi-mysql nagios-plugins-all nagios-plugins-nrpe")
    general.x("yum -y install mysql-server mysql-client libdbi1 libdbi-dev libdbd-mysql")
    general.x("service mysqld start")
    # Create database with icinga user
    general.x("mysql < /opt/syco/var/icinga/icinga_db_create")
    general.x("mysql icinga < /usr/share/doc/icinga-idoutils-libdbi-mysql-1.7.2/db/mysql/mysql.sql")
    # TODO: Figure out password management in some smart way
    general.x("cp -f /opt/syco/usr/syco-private/var/nagios/passwd /etc/icinga/")
    general.x("cp -f /opt/syco/usr/syco-private/var/nagios/icinga.cfg /etc/icinga/icinga.cfg")
    # Harden with iptables
    iptables.add_monitor_chain() 
    # Monitor needs to be able to check itself!
    install_nrpe(args)
    hostList = _get_host_list()
    #_append_services(hostList)
    _move_object_base_structure_icinga()
    _write_hosts_config_icinga(hostList)
    _install_server_plugins()
    return True

def _reload_icinga(args):
    hostList = _get_host_list()
    #_append_services(hostList)
    _move_object_base_structure_icinga()
    _write_hosts_config_icinga(hostList)
    _install_server_plugins()
    return True

def _install_icinga_web():
    """
    This installs the icinga web module. Only source of complexity is moking icinga accessible frmo the document root. 
    """
    general.x("yum install -y  php php-cli php-pear php-xmlrpc php-xsl php-pdo php-soap php-gd php-ldap php-mysql")
    general.x("yum install -y icinga-web")
    general.x("mysql < /opt/syco/var/icinga/icinga-web_db_create")
    general.x("mysql icinga_web  < /usr/share/doc/icinga-web-1.7.2/schema/mysql.sql")
    general.x("mysql < /opt/syco/usr/syco-private/var/nagios/icinga_password.sql")
    # Configure apache to use icinga-directory as document root
    # Let apache read .htacces-files in /usr/share/icinga-web allowoverride for documentroot (but not globally for server, i.e PNP-dir etc)
    # This will might break your http-confg if run twice or on machine with virtualhosts (hence the backup)
    general.x("awk '/AllowOverride None/{c++;if(c==2){sub(\"AllowOverride None\",\"AllowOverride All\");c=0}}1' /etc/httpd/conf/httpd.conf > /tmp/httpd.conf")
    general.set_config_property("/tmp/httpd.conf","/var/www/html","/usr/share/icinga-web/pub", False)
    general.x("mv /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.sycobackup")
    general.x("mv /tmp/httpd.conf /etc/httpd/conf/httpd.conf")
    # Let icinga know its cgi-dir has changed externally
    general.set_config_property("/etc/icinga-web/conf.d/icinga.xml","<!--","<setting name=\"appkit.web_path\">/</setting><!--", False)
    # Make install stateful
    general.set_config_property("/etc/sysconfig/selinux", "SELINUX=enforcing", "SELINUX=permissive")
    general.x("/sbin/chkconfig --level 3 httpd on")
    general.x("/sbin/chkconfig --level 3 mysqld on")
    # Harden with iptables-chain
    iptables.add_httpd_chain()
    return True

def _install_icinga(args):
    '''
    The icinga-installation is divided into two parts - icinga core and icinga web. Icinga core insatlls the icinga-poller (baically 
    an exakt for of the Nagios poller except with SQL integration). Icinga-core also includes a very simple GUI that is kept as a backup
    in case the fancier GUI goes down for any reason. Icinga-web is the "bells and whistles" GUI which is heavier, with "improved" looks 
    and more functionality. 
    '''
    _install_icinga_core(args)
    _install_icinga_web()  
    general.x("service ido2db start")
    general.x("service nrpe start")
    general.x("service icinga start")
    general.x("service httpd start")
    return True

def _install_nrpe(args):
    '''
    The nrpe installation is quite standard - except that the stock NRPE.conf is replaced with a prepped one. After being moved
    the prepped file also has the IP of the monitor server added, so that the server only listens to this IP. Not super safe but
    better than nothing. Also, argument parsing is _disabled_. 
    '''
    install.epel_repo()
    hostList = _get_host_list() 
    # Confusing that nagios-plugins-all does not really include all plugins
    general.x("yum install nagios-plugins-all nrpe nagios-plugins-nrpe php-ldap nagios-plugins-perl perl-Net-DNS perl-Proc-ProcessTable perl-Date-Calc -y")
    # Move object structure and prepare conf-file
    general.x("rm -rf /etc/nagios/nrpe.d")
    general.x("rm -rf /etc/nagios/nrpe.cfg")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/nrpe.d /etc/nagios/")
    general.x("cp /opt/syco/usr/syco-private/var/nagios/nrpe.cfg /etc/nagios/")
    # Extra plugins installed
    _install_nrpe_plugins()
    app.print_verbose("Setting monitor server:" + config.general.get_monitor_server())
    # Allow only monitor to query NRPE
    general.set_config_property("/etc/nagios/nrpe.cfg", "MONITORIP" ,config.general.get_monitor_server(),False)
    app.print_verbose("Setting front-resolver IP to:" +config.general.get_front_resolver_ip())
    # Figure out what servers to query. 
    general.set_config_property("/etc/nagios/nrpe.d/common.cfg", "INTERNALDNS" ,config.general.get_front_resolver_ip(),False)
    general.x("/sbin/chkconfig --level 3 nrpe on")
    general.x("service nrpe start")

def _install_server_plugins():
    # These are plugins for the Icinga-server, no need for install on hosts. 
    general.x("chmod +x /opt/syco/lib/nagios/plugins_snmp/*")
    general.x("cp -p /opt/syco/lib/nagios/plugins_snmp/* /usr/lib64/nagios/plugins/")


def _install_pnp4nagios(args):
    '''
    PNP4Nagios is design to work with Nagios - some hacking is needed to make it play nice with icinga, especially with file permissions
    creating files that the EPEL-package has missed. PNP4Nagios uses the NPCD-daemon to spool data from Icinga to Round Robin Databases. I.e 
    using bulk mode, see http://docs.pnp4nagios.org/_detail/bulk.png

    '''
    # Get packages from epel repo
    install.epel_repo()
    general.x("yum install -y pnp4nagios icinga-web-module-pnp")
    # Pnp4 uses the nagios password file, which will not exist
    general.set_config_property("/etc/httpd/conf.d/pnp4nagios.conf","AuthName \"Nagios Access\"","AuthName \"Icinga Access\"", False)
    general.set_config_property("/etc/httpd/conf.d/pnp4nagios.conf","AuthUserFile /etc/nagios/passwd","AuthUserFile /etc/icinga/passwd",False)
    # NPCD config prepped to work with icinga instead of nagios
    general.x("cp /opt/syco/usr/syco-private/var/nagios/npcd.cfg /etc/pnp4nagios/npcd.cfg")
    # Package-maker forgot to create a log for process-perfdata. PBP goes bonkers if it can't find it
    general.x("touch /var/log/pnp4nagios/perfdata.log")
    # Since we are using icinga (not nagios) we need to change permissions. 
    general.x("usermod -a -G nagios icinga")
    #general.x("chown -R icinga:icinga /var/log/pnp4nagios")
    #general.x("chown -R icinga:icinga /var/spool/pnp4nagios")
    #general.x("chown -R icinga:icinga /var/lib/pnp4nagios")
    # Set npcd (bulk parser/spooler) to auto-start 
    general.x(" /sbin/chkconfig --level 3 npcd on")
    # Restart everything
    general.x("service icinga restart")
    general.x("service httpd restart")
    general.x("service npcd restart")


def _install_nrpe_plugins():
    general.x("chmod +x /opt/syco/lib/nagios/plugins_nrpe/*")
    general.x("cp -p /opt/syco/lib/nagios/plugins_nrpe/* /usr/lib64/nagios/plugins/")


def _move_object_base_structure_icinga():
    """
    Clear the icinga example object fiels. Move the icinga prepped icinga base structure from syco-private to /etc/icinga/ . 
    """
    general.x("rm -rf /etc/icinga/objects/*")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/objects/ /etc/icinga/")


def _write_hosts_config_icinga(serverList):
    """
    We open the nagios host-config file and formatted string for every host in the serverList that has been prepped previously. 
    """
    FILE = open("/etc/icinga/objects/hosts/virtual_host_list.cfg", "w+")
    for host in serverList:
        groups = host.services
        groups.append(host.type)
        hostgroups = ",".join(str(x) for x in groups)
        FILE.writelines("define host{\nhost_name  " + host.name + "\nalias " + host.name + "\naddress " + host.ip + "\nuse " + host.type +"\nhostgroups " + hostgroups + "\n}\n\n")
    FILE.close()
    general.set_config_property("/etc/icinga/objects/hosts/switch_list.cfg", "SWITCHIP" ,config.general.get_switch_back_ip(),False)


class host():

    def __init__(self,configname,configip,hosttype):
        self.name = configname
        self.ip = configip
        self.type = hosttype
        self.services = []



