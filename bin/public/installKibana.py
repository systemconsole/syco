#!/usr/bin/env python
"""
Install a kibana webb server on local server



"""

__author__ = "mattias.hemmingsson@fareoffice.com"
__copyright__ = "Copyright 2015, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "mattias.hemmingsson@fareoffice.com"
__credits__ = [""]
__license__ = ""
__version__ = "1.0.0"
__status__ = "Production"


from general import x
from iptables import InboundFirewallRule


def build_commands(commands):
    commands.add("install-kibana",             install_kibana, "Install or update kibana on server",
                 firewall_config=[InboundFirewallRule(service="kibana", ports=["5601"])])
    commands.add("uninstall-kibana",           uninstall_kibana,           help="Uninstall kibana from host")


def install_kibana(args):
    """
    Install Kibana on local server use like 'syco install-kibana 4.0.2' for installing kibana version 4.0.2
    """
    if len(args) != 2:
        raise Exception("syco install-kibana [version] ")
    x('yum install wget -y')
    #Clean out old kibana
    x('rm -rf /var/www/kibana*')
    #Installin the new kibana
    x('mkdir -p /var/www')
    x('wget https://download.elastic.co/kibana/kibana/kibana-{0}-linux-x64.tar.gz -O /tmp/kibana.tar.gz'.format(args[1]))
    x('tar -zxvf /tmp/kibana.tar.gz -C /var/www/')
    x('ln -s /var/www/kibana-* /var/www/kibana')
    #Adding startup script for kibana
    x('cp /opt/syco/var/kibana/kibana /etc/init.d/')
    x('chmod 774 /etc/init.d/kibana')
    x('chkconfig --add kibana')
    x('chkconfig kibana on')
    x('/etc/init.d/kibana start')


def uninstall_kibana(args):
    """
    Uninstall kibana from server
    """
    x('rm -rf /var/www/kibana*')
    x('chkconfig --del kibana')
    x('rm -rf /etc/init.d/kibana')
