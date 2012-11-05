#!/usr/bin/env python
'''
Nagios installation for new data-centers at TC-Skondal and Availo.

'''

import app
import config
import general
import re
import iptables
import install
import installMysql
import version

# note: perl-Time-HiRes, rrdtool-perl php-gd required for PNP


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
    commands.add("install-icinga", install_icinga, help="Installs a icinga poller and web-interface for monitoring of remote hosts")
    commands.add("reload-icinga", reload_icinga, help="Reloads the icinga object structure.")
    commands.add("install-nagios", install_nagios, help="Installs a nagios poller and web-interface for monitoring of remote hosts")
    commands.add("install-nrpe", install_nrpe, help="Installs NRPE daemon and nagios plugins for monitoring by remote server")
    commands.add("install-pnp4nagios", install_pnp4nagios, help="Install pnp4nagios")


def install_icinga(args):
    app.print_verbose("Installing icinga")
    version_obj = version.Version("installIcinga", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_icinga(args)
    version_obj.mark_executed()

def reload_icinga(args):
    # No verson checking since its not an install/uninstall
    app.print_verbose("Reloading icinga")
    _reload_icinga(args)

def install_nagios(args):
    app.print_verbose("Installing nagios")
    version_obj = version.Version("installNagios", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_nagios(args)
    version_obj.mark_executed()

def install_nrpe(args):
    app.print_verbose("Installing nrpe")
    version_obj = version.Version("installNrpe", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_nrpe(args)
    version_obj.mark_executed()

def install_pnp4nagios(args):
    app.print_verbose("Installing pnp4nagios")
    version_obj = version.Version("install_pnp4nagios", SCRIPT_VERSION)
    version_obj.check_executed()
    _install_pnp4nagios(args)
    version_obj.mark_executed() 


def _append_services(hostList):
    for host in hostList:
        if host.type != "switch":    
            nrpe_return = general.x("/usr/lib64/nagios/plugins/check_nrpe -H " + host.ip + " -c get_services").split()
            if (nrpe_return.pop(0) == "OK"):
                host.services = nrpe_return
            else:
                app.print_verbose(host.name + " is not running NRPE, omitted")
    return hostList

def _get_host_list():
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

def _install_plugins():
    # These are plugins for the ICINGA-server, no need for install on hosts. 
    general.x("chmod +x /opt/syco/lib/nagios/plugins_snmp/*")
    general.x("cp -p /opt/syco/lib/nagios/plugins_snmp/* /usr/lib64/nagios/plugins/")

def _install_icinga_core(args):
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
    _install_plugins()
    return True

def _reload_icinga(args):
    hostList = _get_host_list()
    #_append_services(hostList)
    _move_object_base_structure_icinga()
    _write_hosts_config_icinga(hostList)
    _install_plugins()
    return True

def _install_icinga_web():
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
    general.set_config_property("/usr/share/icinga-web/app/config/icinga.xml","<setting name=\"appkit.web_path\">/icinga-web</setting>","<setting name=\"appkit.web_path\">/</setting>", False)
    # Harden with iptables
    iptables.add_httpd_chain()


    return True

def _install_nagios(args):
    # Everything - todo: use installhttpd and figure out stuff on mod_security.  
    general.x("setenforce 0")
    general.x("yum install httpd php -y")
    general.x("yum install nagios nagios-plugins-all nrpe nagios-plugins-nrpe -y")
    # Copy password file (so we done need to mess around with expect)
    general.x("cp -f /opt/syco/usr/syco-private/var/nagios/passwd /etc/nagios/")
    general.x("cp -f /opt/syco/usr/syco-private/var/nagios/nagios.cfg /etc/nagios/")
    iptables.add_monitor_chain()
    iptables.add_httpd_chain()
    hostList = _get_host_list()
    _append_services(hostList)
    _move_object_base_structure_nagios()
    _write_hosts_config_nagios(hostList)
    _install_plugins()
    general.x("service httpd restart")

def _install_icinga(args):
    # Install icinga.
    # Core features the icinga poller (basically same as nagios), simple CGI GUI, and mysql-binds
    # Web features bells-and-whitles API
    _install_icinga_core(args)
    _install_icinga_web()  
    general.x("service ido2db start")
    general.x("service nrpe start")
    general.x("service icinga start")
    general.x("service httpd start")
    return True

def _install_nrpe(args):
    install.epel_repo()
    hostList = _get_host_list() 
    # Confusing that nagios-plugins-all does not really include all plugins
    general.x("yum install nagios-plugins-all nrpe nagios-plugins-nrpe php-ldap nagios-plugins-perl perl-Net-DNS perl-Proc-ProcessTable perl-Date-Calc -y")
    # Move object structure and prepare conf-file
    general.x("rm -rf /etc/nagios/nrpe.d")
    general.x("rm -rf /etc/nagios/nrpe.cfg")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/nrpe.d /etc/nagios/")
    general.x("cp /opt/syco/usr/syco-private/var/nagios/nrpe.cfg /etc/nagios/")
    general.x("chmod +x /opt/syco/lib/nagios/plugins_nrpe/*")
    general.x("cp -p /opt/syco/lib/nagios/plugins_nrpe/* /usr/lib64/nagios/plugins/")
    app.print_verbose("Setting monitor server:" + config.general.get_monitor_server())
    general.set_config_property("/etc/nagios/nrpe.cfg", "MONITORIP" ,config.general.get_monitor_server(),False)
    app.print_verbose("Setting front-resolver IP to:" +config.general.get_front_resolver_ip())
    general.set_config_property("/etc/nagios/nrpe.d/common.cfg", "INTERNALDNS" ,config.general.get_front_resolver_ip(),False)
    general.x("service nrpe start")

def _install_pnp4nagios(args):
    # Using bulk mode, see http://docs.pnp4nagios.org/_detail/bulk.png?id=pnp-0.6%3Aconfig
    # Get packages from epel repo
    install.epel_repo()
    general.x("yum install -y pnp4nagios")
    # Pnp4 uses the nagios password file, just link it over (easier then messing around with all the CGI-bins and httpd-confs)
    # TODO: mess around with the CGI's and httpd-conf
    general.x("mv /etc/nagios/passwd /etc/nagios/passwd.sycobackup")
    general.x("rm -f /etc/nagios/passwd")
    general.x("ln -s /etc/icinga/passwd /etc/nagios/passwd")
    general.x("yum install -y icinga-web-module-pnp") 
    general.x("cp /opt/syco/usr/syco-private/var/nagios/npcd.cfg /etc/pnp4nagios/npcd.cfg")
    # Package-maker forgot to create a log for process-perfdata. Goes bonkers if it can't find it
    general.x("touch /var/log/pnp4nagios/perfdata.log")
    # Since we are using icinga we need to change permissions. 
    # Option would be to change group, but then some permissions would still be lost
    general.x("chown -R icinga:icinga /var/log/pnp4nagios")
    general.x("chown -R icinga:icinga /var/spool/pnp4nagios")
    general.x("chown -R icinga:icinga /var/lib/pnp4nagios")
    # Restart everything
    general.x("service icinga restart")
    general.x("service npcd start")
    general.x("service httpd restart")



def _move_object_base_structure_nagios():
    general.x("rm -rf /etc/nagios/objects/*")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/objects/ /etc/nagios/")

def _move_object_base_structure_icinga():
    general.x("rm -rf /etc/icinga/objects/*")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/objects/ /etc/icinga/")

def _write_hosts_config_nagios(serverList):
    FILE = open("/etc/nagios/objects/hosts/virtual_host_list.cfg", "w+")
    for host in serverList:
        groups = host.services
        groups.append(host.type)
        hostgroups = ",".join(str(x) for x in groups)
        FILE.writelines("define host{\nhost_name  " + host.name + "\nalias " + host.name + "\naddress " + host.ip + "\nuse " + host.type +"\nhostgroups " + hostgroups + "\n}\n\n")
    FILE.close()



def _write_hosts_config_icinga(serverList):
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



