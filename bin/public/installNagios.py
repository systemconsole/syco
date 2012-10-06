#!/usr/bin/env python
'''
Nagios installation for new data-centers at TC-Skondal and Availo.


 notes on getting nagios to actually install
 
 Nagios has been moved to the extended repositories - what is the quality of EPEL
 Compiling isnt rocket science though
 Follow http://www.unixmen.com/how-to-install-nagios-in-rhel-centos-fedora/
 - a yum install openssl-devel was needed for plugins to compile
 - a chcon -R -t httpd_sys_content_t /usr/local/nagios was also needed, yey for SELinux
 - it won't play nice with mod security - lets just use vanilla apache + php for nowq
 http://linuxscribbles.blogspot.se/2012/06/how-to-install-nagios-on-rhel-6-centos.html another guide

'''

import app
import config
import general
import re

__author__ = "elis.kullberg@netlight.com"
__copyright__ = "Copyright 2012, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Elis Kullberg"
__email__ = "above"
__credits__ = ["Daniel & Mattias"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Development"


def build_commands(commands):
    commands.add("install-nagios", install_nagios, help="Installs a nagios poller and web-interface")


def install_nagios(args):
    serverList = get_network_config()
    move_object_base_structure()
    write_hosts_config(serverList)

def write_hosts_config(serverList):
    FILE = open("/usr/local/nagios/etc/objects/hosts/virtual_host_list.cfg", "w")
    for host in serverList:
        FILE.writelines("define host{\nhost_name  " + host.name + "\nalias " + host.name + "\naddress " + host.ip + "\nuse " + host.type +"\nhostgroups " + host.type+ "\n}\n\n")
    FILE.close()

def get_network_config():
    serverList=[]
    app.print_verbose("Starting Nagios installation process")
    for server in config.get_servers():
        if bool(re.search('fw', server)):
            serverList.append(host(server, config.host(server).get_front_ip(),"physical_host"))
        elif bool(re.search('switch', server)): 
            serverList.append(host(server, config.host(server).get_front_ip(),"switch"))
        else : 
            serverList.append(host(server, config.host(server).get_front_ip(),"virtual_host"))
    return serverList

def move_object_base_structure():
    general.x("rm -r /usr/local/nagios/etc/objects")
    general.x("cp -r /opt/syco/usr/syco-private/var/nagios/objects/ /usr/local/nagios/etc/objects")

class host():

    def __init__(self,configname,configip,hosttype):
        self.name = configname
        self.ip = configip
        self.type = hosttype



