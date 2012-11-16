#!/usr/bin/env python
'''
Network related functions.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import fcntl
import array
import struct
import socket
import platform

def get_interface_ip(ifn):
    '''
    Get ip from a specific interface.

    Example:
    ip = get_interface_ip("eth0")

    '''
    import socket, fcntl, struct
    sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip = socket.inet_ntoa(fcntl.ioctl(sck.fileno(),0x8915,struct.pack('256s', ifn[:15]))[20:24])
    except:
        ip = None
    return ip

all_interfaces = None
def get_all_interfaces():
    """
    Used to get a list of the up interfaces and associated IP addresses
    on this machine (linux only).

    Returns:
        Dictionary where key is the interface name, and value is the ip.
    """
    global all_interfaces
    if all_interfaces:
        return all_interfaces

    f = open('/proc/net/dev','r')
    ifacelist = f.read().split('\n')
    f.close()

    # remove 2 lines header
    ifacelist.pop(0)
    ifacelist.pop(0)

    all_interfaces = {}
    # loop to check each line
    for line in ifacelist:

        ifacedata = line.replace(' ','').split(':')

        # check the data have 2 elements
        if len(ifacedata) == 2:
            all_interfaces[ifacedata[0]] = get_interface_ip(ifacedata[0])

    return all_interfaces

# Cache variable for lan_ip
lan_ip = ""

def get_lan_ip():
    '''
    Get one of the external ips on the computer.

    Prioritize ips from interface in the following orders
    "br0", "bond0", "eth0", "eth1", "br1", "bond1", "eth2", "eth3"

    '''
    global lan_ip
    if (lan_ip==""):
        try:
            lan_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass

        if lan_ip == "" or (lan_ip.startswith("127.") and os.name != "nt"):
            interfaces = ["br0", "bond0", "br1", "bond1",
                          "eth0", "eth1", "eth2", "eth3"]

            interface_list = get_all_interfaces()
            for ifname in interfaces:
                if ifname in interface_list:
                   lan_ip = interface_list[ifname]
                   break

    return lan_ip

# Cache variable for public_ip
public_ip = ""

def get_public_ip():
    '''
    Get one of the external ips on the computer.

    Prioritize ips from interface in the following orders
    "br1", "bond1", "eth1"

    '''
    global public_ip
    if (public_ip == ""):
        if public_ip == "" or (public_ip.startswith("127.") and os.name != "nt"):
            interfaces = ["br1", "bond1", "eth1"]

            interface_list = get_all_interfaces()
            for ifname in interfaces:
                if ifname in interface_list:
                   public_ip = interface_list[ifname]
                   break

    return public_ip
def reverse_ip(str):
    '''Reverse an ip from 1.2.3.4 to 4.3.2.1'''
    reverse_str=""
    for num in str.split("."):
        if (reverse_str):
            reverse_str = "." + reverse_str
        reverse_str = num + reverse_str
    return reverse_str

def get_ip_class_c(ip):
    '''Get a class c net from an ip. 1.2.3.4 will return 1.2.3'''
    new_ip = ""
    split_ip = ip.split(".")
    for i in range(3):
        if (new_ip):
            new_ip += "."
        new_ip = new_ip + split_ip[i]

    return new_ip

def num_of_eth_interfaces():
    counter = 0
    interface_list = get_all_interfaces()
    for ifname in interface_list:
        if "eth" in ifname:
            counter += 1
    return counter

def get_hostname():
    return os.uname()[1]

if (__name__ == "__main__"):
    print "get_all_interfaces " + str(get_all_interfaces())
    print "get_interface_ip eth0 " + str(get_interface_ip("eth0"))
    print "get_interface_ip br0 " + str(get_interface_ip("br0"))
    print "get_interface_ip none " + str(get_interface_ip("none"))
    print "get_lan_ip " + get_lan_ip()
    print "reverse_ip " + reverse_ip("1.2.3.4")
    print "get_ip_class_c " + get_ip_class_c("1.2.3.4")
    print "num_of_eth_interfaces " + str(num_of_eth_interfaces())
    print "get_hostname " + get_hostname()

def setup_bond(bond, bridge):
    """
    Setup a bondX device.

    Will use mode: active-backup or 1
    - Sets an   policy for fault tolerance. Transmissions are
    received and sent out via the first available bonded slave interface.
    Another bonded slave interface is only used if the active bonded slave
    interface fails.

    READ MORE
    http://www.kernel.org/doc/Documentation/networking/bonding.txt

    """
    general.store_file("/etc/sysconfig/network-scripts/ifcfg-" + bond,
"""DEVICE=%s
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
    filename = "/etc/sysconfig/network-scripts/ifcfg-" + eth
    mac = general.get_config_value(filename, "HWADDR")
    general.store_file(filename,
"""DEVICE="%s"
HWADDR=%s
MASTER=%s
SLAVE=yes
NM_CONTROLLED="no"
ONBOOT=yes
USERCTL=no
HOTPLUG=no
BOOTPROTO=none
""" % (eth, mac, bond))

def setup_bridge(bridge, ip, netmask, gateway, resolver):
    '''
    Bridge the bond network with the KVM guests.

    Can work both with and without IP.

    '''
    content = """DEVICE=%s
TYPE=Bridge
ONBOOT=yes
USERCTL=no
DELAY=0
BOOTPROTO=none
""" % (bridge)

    if ip:
        broadcast = net.get_ip_class_c(ip) + ".255"
        network = net.get_ip_class_c(ip) + ".0"

        content = content + """IPADDR=%s
NETMASK=%s
NETWORK=%s
BROADCAST=%s""" % (ip, netmask, network, broadcast)

    if gateway:
        content += "\nGATEWAY=" + gateway

    if resolver:
        content += "\nDNS=" + resolver

    general.store_file("/etc/sysconfig/network-scripts/ifcfg-" + bridge, content)
