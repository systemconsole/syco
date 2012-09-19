#!/usr/bin/env python
'''
Install DHCP Server

This dhcp server is mainly used to get KVM guest installation to work with
kickstarts.

http://www.yolinux.com/TUTORIALS/DHCP-Server.html
http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch08_:_Configuring_the_DHCP_Server
http://www.howtoforge.com/dhcp_server_linux_debian_sarge

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import shutil
import net

import app
import general
import version


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("install-dhcp-server", install_dhcp, help="Install a dhcp server on the current server.")
    commands.add("uninstall-dhcp-server", uninstall_dhcp, help="Uninstall the dhcp server on the current server.")


def install_dhcp(args):
    '''
    Install a dhcp server on the current server.

    '''
    app.print_verbose("Install DHCP-Server version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallDHCPServer", SCRIPT_VERSION)
    version_obj.check_executed()

    general.shell_exec("yum -y install dhcp")
    general.shell_exec("/sbin/chkconfig dhcpd on")
    shutil.copyfile(app.SYCO_PATH + "/var/dhcp/dhcp3.conf", "/etc/dhcp/dhcpd.conf")
    general.set_config_property("/etc/dhcp/dhcpd.conf", "\$\{IP\}", net.get_ip_class_c(net.get_lan_ip()))
    general.set_config_property("/etc/sysconfig/dhcpd", ".*DHCPDARGS.*", "DHCPDARGS=%s" % get_back_interface())
    general.shell_exec("service dhcpd restart")

    version_obj.mark_executed()


def get_back_interface():
    '''
    Get interface used for back net.

    If br0 has an ip that is the backnet device, otherwise it's eth0.

    '''
    if net.get_interface_ip("br0") == None:
      iface = 'eth0'
    else:
      iface = 'br0'

    return iface


def uninstall_dhcp(args):
    general.shell_exec("service dhcpd stop")
    general.shell_exec("/sbin/chkconfig dhcpd off")
    general.shell_exec("rm /etc/dhcp/dhcpd.conf")
    general.set_config_property("/etc/sysconfig/dhcpd", ".*DHCPDARGS.*", "DHCPDARGS=")
    general.shell_exec("yum -y erase dhcp")

    version_obj = version.Version("InstallDHCPServer", SCRIPT_VERSION)
    version_obj.mark_uninstalled()
