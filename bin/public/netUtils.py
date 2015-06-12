#!/usr/bin/env python
'''
Cmdline tools used to manipulate the network on a host.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from app import print_verbose
from general import x
from scopen import scOpen
import app
import config
import general
import install
import net
import version
import math


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


def build_commands(commands):
    commands.add("net-setup-bond-br", net_setup_bond_br, help="Setup bonded bridge interfaces.")


def net_setup_bond_br(args):
    """
    Setup bonded network interfaces and bridges.

    This must work together with a virtual host using KVM.

    Read more.
    http://serverfault.com/questions/316623/what-is-the-correct-way-to-setup-a-bonded-bridge-on-centos-6-for-kvm-guests
    http://www.linuxfoundation.org/collaborate/workgroups/networking/bridge
    http://www.cyberciti.biz/faq/rhel-linux-kvm-virtualization-bridged-networking-with-libvirt/
    http://www.linux-kvm.org/page/HOWTO_BONDING
    https://fedorahosted.org/cobbler/wiki/VirtNetworkingSetupForUseWithKoan
    http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization/sect-Virtualization-Network_Configuration-Bridged_networking_with_libvirt.html
    http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/s1-networkscripts-interfaces.html
    http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Deployment_Guide/sec-Using_Channel_Bonding.html

    """
    app.print_verbose("Install bonded bridges host version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("NetSetupBondBr", SCRIPT_VERSION)
    version_obj.check_executed()

    #
    app.print_verbose(
        "Install yum package with all tools that is required to setup bridges."
    )
    install.package("bridge-utils")

    #
    print_verbose(
        "Setup modprobe alias for bonding, don't know exactly why we need to " +
        "do that. Maybe because the ifcfg files referars to bond0 instead of " +
        "bonding, or because it loads the module bonding at the same time as " +
        "the alias is created."
    )
    sycoConf = scOpen("/etc/modprobe.d/syco.conf")
    sycoConf.remove("alias bond.*")
    sycoConf.add("alias bond0 bonding")

    # Get all parameters from syco config.
    # Check if interfaces are defined, otherwise fall back to autodetecting
    front_interfaces = config.host(net.get_hostname()).get_front_interfaces()
    back_interfaces = config.host(net.get_hostname()).get_back_interfaces()

    num_of_if = len(front_interfaces) + len(back_interfaces)
    if num_of_if == 0:
        # Autodetect
        num_of_if = net.num_of_eth_interfaces()
        
    front_ip = config.host(net.get_hostname()).get_front_ip()
    front_netmask = config.general.get_front_netmask()
    front_gw = config.general.get_front_gateway_ip()
    front_resolver = config.general.get_front_resolver_ip()
    net_count = 1

    if config.general.is_back_enabled():
        back_ip = config.host(net.get_hostname()).get_back_ip()
        back_netmask = config.general.get_back_netmask()
        back_gw = config.general.get_back_gateway_ip()
        back_resolver = config.general.get_back_resolver_ip()
        net_count += 1

    eth_count = 0;
    if len(front_interfaces) < 1:
        # Use default eth interfaces
        # Also, if you don't specify front net interfaces, you may not specify back net interfaces.
        if_per_net_count = int(math.floor(num_of_if / net_count))

        if net_count > 1:
            back_interfaces = []
            for i in range(if_per_net_count):
                back_interfaces.append("eth" + str(eth_count))
                eth_count += 1

        front_interfaces = []
        for i in range(if_per_net_count):
            front_interfaces.append("eth" + str(eth_count))
            eth_count += 1

    app.print_verbose("Configuring front net bond bond1 with interfaces: {0}".format(front_interfaces))
    setup_bridge("br1", front_ip, front_netmask, front_gw, front_resolver)
    setup_bond("bond1", "br1")
    for front_interface in front_interfaces:
        setup_eth(front_interface, "bond1")

    if net_count == 2:
        app.print_verbose("Found back-net configuration, configuring second bond bond0 with interfaces: {0}".format(back_interfaces))
        setup_bridge("br0", back_ip, back_netmask, back_gw, back_resolver)
        setup_bond("bond0", "br0")
        for back_interface in back_interfaces:
            setup_eth(back_interface, "bond0")

    #
    app.print_verbose(
        "Restart the network service so all changes will be applied."
    )
    x("service network restart")
    x("echo \"nameserver 8.8.8.8\" > /etc/resolv.conf")

    #
    version_obj.mark_executed()


def setup_bridge(bridge, ip, netmask, gateway, resolver):
    '''
    Bridge the bond network with the KVM guests.

    Can work both with and without IP.

    For info on mcsnoop see:
        http://thread.gmane.org/gmane.linux.network/153338

    '''
    content = """# Generated by syco
DEVICE={0}
TYPE=Bridge
ONBOOT=yes
USERCTL=no
DELAY=0
BOOTPROTO=none
""".format(bridge)

    if ip:
        broadcast = net.get_broadcast_address(ip, netmask)
        network = net.get_network_address(ip, netmask)

        content =  """{0}IPADDR={1}
NETMASK={2}
NETWORK={3}
BROADCAST={4}
BRIDGING_OPTS="setmcsnoop=0"
""".format(content, ip, netmask, network, broadcast)

    if gateway:
        content += "GATEWAY={0}\n".format(gateway)

    if resolver:
        content += "DNS={0}\n".format(resolver)

    general.store_file("/etc/sysconfig/network-scripts/ifcfg-" + bridge, content)


def setup_bond(bond, bridge):
    """
    Setup a bondX device.

    """
    app.print_verbose("Setup bonded device {0} for bridge {1}".format(bond, bridge))
    app.print_verbose(
        "Will use mode: active-backup or 1\n" +
        "- Sets an active-backup policy for fault tolerance. Transmissions are " +
        "received and sent out via the first available bonded slave interface. " +
        "Another bonded slave interface is only used if the active bonded slave " +
        "interface fails."
    )

    general.store_file("/etc/sysconfig/network-scripts/ifcfg-" + bond,
"""# Generated by syco
DEVICE=%s
BRIDGE=%s
BONDING_OPTS="miimon=100 mode=active-backup"
ONBOOT=yes
USERCTL=no
ONPARENT=yes
BOOTPROTO=none
""" % (bond, bridge))


def setup_eth(eth, bond):
    '''
    Setup the eth interface to be included in a bond.

    '''
    app.print_verbose(
        "Setup the eth interface {0} to be included in {1}.".format(
            eth, bond
        )
    )
    filename = "/etc/sysconfig/network-scripts/ifcfg-" + eth
    mac = general.get_config_value(filename, "HWADDR")
    general.store_file(filename,
"""# Generated by syco
DEVICE="%s"
HWADDR=%s
MASTER=%s
SLAVE=yes
NM_CONTROLLED="no"
ONBOOT=yes
USERCTL=no
HOTPLUG=no
BOOTPROTO=none
""" % (eth, mac, bond))
