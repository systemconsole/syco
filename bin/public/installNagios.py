#!/usr/bin/env python
'''
Nagios installation for new data-centers at TC-Skondal and Availo.

'''

import app
import config
import general
import re
import iptables

__author__ = "elis.kullberg@netlight.com"
__copyright__ = "Copyright 2012, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Elis Kullberg"
__email__ = "above"
__credits__ = ["Daniel & Mattias"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Development"


def build_commands(commands):
    commands.add("install-icinga", install_icinga, help="Installs a icinga poller and web-interface for monitoring of remote hosts")
    commands.add("install-nagios", install_nagios, help="Installs a nagios poller and web-interface for monitoring of remote hosts")
    commands.add("install-nrpe", install_nrpe, help="Installs NRPE daemon and nagios plugins for monitoring by remote server")

def install_nagios(args):
    # Everything - todo: use installhttpd and figure out stuff on mod_security.  
    general.x("setenforce 0")
    #general.x("yum install httpd php -y")
    #general.x("yum install nagios nagios-plugins-all nrpe nagios-plugins-nrpe -y")
    # Copy password file (so we done need to mess around with expect)
    general.x("cp -f /opt/syco/usr/syco-private/var/nagios/passwd /etc/nagios/")
    general.x("cp -f /opt/syco/usr/syco-private/var/nagios/nagios.cfg /etc/nagios/")
    iptables.add_monitor_chain()
    iptables.add_httpd_chain()
    hostList = get_host_list()
    append_services(hostList)
    move_object_base_structure_nagios()
    write_hosts_config_nagios(hostList)
    install_plugins()
    general.x("service httpd restart")

def install_icinga(args):
    # Add instalation steps - sql schemas will suck to install
    general.x("setenforce 0")
    general.x("cp -f /opt/syco/usr/syco-private/var/nagios/passwd /etc/icinga/")
    general.x("cp -f /opt/syco/usr/syco-private/var/nagios/nagios.cfg /etc/icinga/icinga.cfg")
    iptables.add_monitor_chain()
    iptables.add_httpd_chain()
    hostList = get_host_list()
    append_services(hostList)
    move_object_base_structure_icinga()
    write_hosts_config_icinga(hostList)
    install_plugins()
    general.x("service httpd restart")

def _install_icinga_web():
    return True

def _install_icinga_core():
    return True


def append_services(hostList):
    for host in hostList:
        if host.type != "switch":    
            nrpe_return = general.x("/usr/lib64/nagios/plugins/check_nrpe -H " + host.ip + " -c get_services").split()
            if (nrpe_return.pop(0) == "OK"):
                host.services = nrpe_return
            else:
                app.print_verbose(host.name + " is not running NRPE, omitted")
    return hostList

def install_nrpe(args):
    hostList = get_host_list() 
    # Confusing that nagios-plugins-all does not really include all plugins
    # If script breaks here EPEL is probably not activated
    general.x("yum install nagios-plugins-all nrpe nagios-plugins-nrpe -y")
    # Move object structure and prepared conf-file
    general.x("rm -rf /etc/nagios/nrpe.d")
    general.x("rm -rf /etc/nagios/nrpe.cfg")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/nrpe.d /etc/nagios/")
    general.x("cp /opt/syco/usr/syco-private/var/nagios/nrpe.cfg /etc/nagios/")
    general.x("cp /opt/syco/usr/syco-private/lib/nagios/plugins/get_services /usr/lib64/nagios/plugins/")   
    # Append the monitor-server IP to this conf-file
    for host in hostList:
        if bool(re.search('monitor', host.name)):
            general.set_config_property("/etc/nagios/nrpe.cfg", "MONITORIP", host.ip, add_if_not_exist=False)
    # Start nrpe!
    general.x("service nrpe start")
    pass

def write_hosts_config_nagios(serverList):
    FILE = open("/etc/nagios/objects/hosts/virtual_host_list.cfg", "w+")
    for host in serverList:
        groups = host.services
        groups.append(host.type)
        hostgroups = ",".join(str(x) for x in groups)
        FILE.writelines("define host{\nhost_name  " + host.name + "\nalias " + host.name + "\naddress " + host.ip + "\nuse " + host.type +"\nhostgroups " + hostgroups + "\n}\n\n")
    FILE.close()

def write_hosts_config_icinga(serverList):
    FILE = open("/etc/icinga/objects/hosts/virtual_host_list.cfg", "w+")
    for host in serverList:
        groups = host.services
        groups.append(host.type)
        hostgroups = ",".join(str(x) for x in groups)
        FILE.writelines("define host{\nhost_name  " + host.name + "\nalias " + host.name + "\naddress " + host.ip + "\nuse " + host.type +"\nhostgroups " + hostgroups + "\n}\n\n")
    FILE.close()

def get_host_list():
    serverList=[]
    app.print_verbose("Starting Nagios/Icinga installation process")
    for server in config.get_servers():
        if bool(re.search('fw', server)) or bool(re.search('vh', server)):
            serverList.append(host(server, config.host(server).get_front_ip(),"physical_host"))
        elif bool(re.search('switch', server)): 
            serverList.append(host(server, config.host(server).get_front_ip(),"switch"))
        else : 
            serverList.append(host(server, config.host(server).get_front_ip(),"virtual_host"))
    return serverList

def install_plugins():
    general.x("cp /opt/syco/lib/nagios/plugins/check_switch_mac_table /usr/lib64/nagios/plugins/")
    general.x("cp /opt/syco/lib/nagios/plugins/check_switch_ports_status /usr/lib64/nagios/plugins/")
    general.x("chmod +x /usr/lib64/nagios/plugins/check_switch_ports_status")
    general.x("chmod +x /usr/lib64/nagios/plugins/check_switch_mac_table")

def move_object_base_structure_nagios():
    general.x("rm -rf /etc/nagios/objects/*")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/objects/ /etc/nagios/")

def move_object_base_structure_icinga():
    general.x("rm -rf /etc/icinga/objects/*")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/objects/ /etc/icinga/")

class host():

    def __init__(self,configname,configip,hosttype):
        self.name = configname
        self.ip = configip
        self.type = hosttype
        self.services = []



