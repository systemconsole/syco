#!/usr/bin/env python
'''
Nagios installation for new data-centers at TC-Skondal and Availo.

'''

import app
import config

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

def get_network_config():
    serverList=[]
    app.print_verbose("Starting Nagios installation process")
    for server in config.get_servers():
        serverList.append(host(server, config.host(server).get_front_ip()))
    return serverList



class host():

    def __init__(self,configname,configip):
        self.name = configname
        self.ip = configip



