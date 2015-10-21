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


import array
import fcntl
import os
import platform
import socket
import struct

from general import x
from scopen import scOpen


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
    "br0", "br1", "bond0", "bond1", "eth0", "eth1",  "eth2", "eth3","eth4", "eth5"

    '''
    global lan_ip
    if (lan_ip==""):
        try:
            lan_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            pass

        if lan_ip == "" or (lan_ip.startswith("127.") and os.name != "nt"):
            interfaces = ["br1", "br0", "bond0", "bond1",
                          "eth0", "eth1", "eth2", "eth3","eth4", "eth5"]

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


def enable_ip_forward(enable=1):
    '''
    Controls IP packet forwarding

    '''
    scOpen("/etc/sysctl.conf").replace_add(
        "^net.ipv4.ip_forward.*$", "net.ipv4.ip_forward = {0}".format(enable)
    )
    x("/sbin/sysctl -w net.ipv4.ip_forward={0}".format(enable))

    # Flush settings.
    x("/sbin/sysctl -w net.ipv4.route.flush=1")
    x("/sbin/sysctl -w net.ipv6.route.flush=1")


def disable_ip_forward():
    '''
    Controls IP packet forwarding

    '''
    enable_ip_forward(0)


def get_network_cidr(dd_ipv4, dd_netmask):
    '''
    Returns proper CIDR (i.e "network-addr"/"24") network address, for arguments
    consisting of any ip within the subnet, and the dot-separated netmask.

    '''
    # Generate network address and CIDR-style netmask
    network_ip = get_network_address(dd_ipv4,dd_netmask)
    netmask_cidr = dd_subnet_to_cidr_subnet(dd_netmask)

    # Return them in a single string
    return "{0}/{1}".format(network_ip,netmask_cidr)


def dd_subnet_to_cidr_subnet(subnet):
    '''
    Converts a dot-decimal separated subnet to a cidr-style subnet
    Definition of cidr: http://en.wikipedia.org/wiki/CIDR_notation

    Ex 255.255.255.0 to 24

    '''
    # Convert octet format from integer to a binary-string (i.e 4 becomes "100")
    subnet_binary_list = ["{0:b}".format(int(s)) for s in subnet.split(".")]
    # For all 4 octets, count the number of ones, and return the count
    one_count = 0
    for octet in subnet_binary_list:
        one_count += octet.count("1")

    return one_count


def get_network_address(dd_ipv4, dd_netmask):
    '''
    Return the network address for any subnet and ip within it.

    Ex 192.168.5.7,255.255.250 to 192.168.5.0

    '''
    # Split both arguments on "." into a int-list
    dd_ipv4_int_list = [int(s) for s in dd_ipv4.split(".")]
    dd_netmask_int_list = [int(s) for s in dd_netmask.split(".")]

    # for every octet in outdata, AND together corresponding octets in dd-indata
    # see http://docs.python.org/2/library/functions.html#zip
    network_address_integers = [x & y for x,y in zip(dd_ipv4_int_list, dd_netmask_int_list)]

    # Return the list as a dot-separated list
    network_address_string = ".".join([str(octet) for octet in network_address_integers])

    return network_address_string


def get_broadcast_address(dd_ipv4, dd_netmask):
    '''
    Return the broadcast address

    '''
    # Make an int-list of both addresses (and invert netmask)
    dd_ipv4_int_list = [int(s) for s in dd_ipv4.split(".")]
    dd_netmask_int_list_inv = [255 - int(s) for s in dd_netmask.split(".")]

    # OR the lists together, and concatenate to a string
    broadcast_address_integers = [x | y for x,y in zip(dd_ipv4_int_list, dd_netmask_int_list_inv)]
    broadcast_address_string = ".".join([str(octet) for octet in broadcast_address_integers])

    # Return the result
    return broadcast_address_string


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
