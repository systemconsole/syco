#!/usr/bin/env python
'''
Install the server to act as a KVM host.

Read more:
http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html-single/Virtualization/
http://www.linuxjournal.com/article/9764
http://www.cyberciti.biz/faq/centos-rhel-linux-kvm-virtulization-tutorial/
http://www.linux-kvm.org
http://wiki.centos.org/HowTos/KVM
http://www.howtoforge.com/virtualization-with-kvm-on-a-fedora-11-server
http://www.redhat.com/promo/rhelonrhev/?intcmp=70160000000IUtyAAG

Use iSCSI
http://berrange.com/posts/2010/05/05/provisioning-kvm-virtual-machines-on-iscsi-the-hard-way-part-1-of-2/
http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html-single/Virtualization/#sect-Virtualization-Storage_Pools-Creating-iSCSI

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
import re
import time

import app
import config
import general
import version
import install
import net
import iptables
import disk

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 3

def build_commands(commands):
    commands.add("install-kvmhost", install_kvmhost, help="Install kvm host on the current server.")

def install_kvmhost(args):
    '''
    The actual installation of the kvm host.

    '''
    app.print_verbose("Install kvm host version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallKvmHost", SCRIPT_VERSION)
    version_obj.check_executed()

    if (not general.grep("/proc/cpuinfo", "vmx|svm")):
        app.print_error("CPU don't support virtualization.")
        _abort_kvm_host_installation()

    if (not general.grep("/proc/cpuinfo", "constant_tsc")):
        app.print_error("CPU don't have a constant Time Stamp Counter.")
        _abort_kvm_host_installation()

    # Install the kvm packages
    install.package("qemu-kvm")
    install.package("libvirt")
    install.package("libguestfs-tools")

    # Provides the virt-install command for creating virtual machines.
    install.package("python-virtinst")

    # Before libvirtd starts, create a snapshot partion for qemu.
    _create_kvm_snapshot_partition()

    # Start virsh
    general.shell_exec("service libvirtd start")

    _enable_ksm()

    # Looks like we need to wait for the libvirtd to start, otherwise
    # the virsh nodeinfo below doesn't work.
    time.sleep(1)

    # Set selinux
    general.shell_exec("setenforce 1")

    # Is virsh started?
    result = general.shell_exec("virsh nodeinfo")
    if "CPU model:" not in result:
        app.print_error("virsh not installed.")
        _abort_kvm_host_installation()

    result = general.shell_exec("virsh -c qemu:///system list")
    if "Id Name" not in result:
        app.print_error("virsh not installed.")
        _abort_kvm_host_installation()

    _setup_network_interfaces()

    iptables.add_kvm_chain()
    iptables.save()

    version_obj.mark_executed()

    # Set selinux
    general.shell_exec("reboot")

    # Wait for the reboot to be executed, so the script
    # doesn't proceed to next command in install.cfg
    time.sleep(1000)

def _create_kvm_snapshot_partition():
    '''
    Create a partion that will be used by kvm/qemu to store guest snapshots.

    Memory snapshots when rebooting and such.

    TODO: Size should be equal to RAM.
    '''
    volgroup = disk.active_volgroup_name()
    devicename = "/dev/" + volgroup + "/qemu"
    result = general.shell_exec("lvdisplay -v " + devicename, output = False)
    if (devicename not in result):
        general.shell_exec("lvcreate -n qemu -L 100G " + volgroup)
        general.shell_exec("mkfs.ext4 -j " + devicename)
        general.shell_exec("mkdir -p /var/lib/libvirt/qemu")
        general.shell_exec("mount " + devicename + " /var/lib/libvirt/qemu")
        general.shell_exec("chown qemu:qemu /var/lib/libvirt/qemu")
        general.shell_exec("restorecon -R -v /var/lib/libvirt/qemu")

        # Automount the new partion when rebooting.
        value = devicename + "        /var/lib/libvirt/qemu     ext4        defaults                1 2"
        general.set_config_property("/etc/fstab", value, value)

def _setup_network_interfaces():
    """
    Setup bonded network interfaces and bridges.

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
    # Remove the virbr0, "NAT-interface".
    # http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization/chap-Virtualization-Network_Configuration.html
    general.shell_exec("virsh net-destroy default")
    general.shell_exec("virsh net-undefine default")
    general.shell_exec("service libvirtd restart")

    # Install network bridge
    install.package("bridge-utils")

    general.set_config_property2("/etc/modprobe.d/syco.conf",
                                 "alias bond0 bonding")

    num_of_if = net.num_of_eth_interfaces()

    front_gw = config.general.get_front_gateway_ip()
    front_resolver = config.general.get_front_resolver_ip()
    front_netmask = config.general.get_front_netmask()
    front_ip = config.host(net.get_hostname()).get_front_ip()

    back_gw = config.general.get_back_gateway_ip()
    back_resolver = config.general.get_back_resolver_ip()
    back_netmask = config.general.get_back_netmask()
    back_ip = config.host(net.get_hostname()).get_back_ip()
    if (num_of_if >= 4):
        # Setup back-net
        _setup_bridge("br0", back_ip, back_netmask, back_gw, back_resolver)
        _setup_bond("bond0", "br0")
        _setup_eth("eth0", "bond0")
        _setup_eth("eth1", "bond0")

        # _setup front-net
        _setup_bridge("br1", front_ip, front_netmask, front_gw, front_resolver)
        _setup_bond("bond1", "br1")
        _setup_eth("eth2", "bond1")
        _setup_eth("eth3", "bond1")
    elif (num_of_if == 2):
        # Setup back-net
        _setup_bridge("br0", back_ip, back_netmask, back_gw, back_resolver)
        _setup_bond("bond0", "br0")
        _setup_eth("eth0", "bond0")

        # _setup front-net
        _setup_bridge("br1", front_ip, front_netmask, front_gw, front_resolver)
        _setup_bond("bond1", "br1")
        _setup_eth("eth1", "bond1")
    else:
        app.print_error("To few network interfaces: " + str(num_of_if))
        _abort_kvm_host_installation()

def _setup_bond(bond, bridge):
    """
    Setup a bondX device.

    Will use mode: active-backup or 1
    - Sets an active-backup policy for fault tolerance. Transmissions are
    received and sent out via the first available bonded slave interface.
    Another bonded slave interface is only used if the active bonded slave
    interface fails.

    """
    general.store_file("/etc/sysconfig/network-scripts/ifcfg-" + bond,
"""DEVICE=%s
BRIDGE=%s
BONDING_OPTS="miimon=100 mode=1"
ONBOOT=yes
USERCTL=no
ONPARENT=yes
BOOTPROTO=none
""" % (bond, bridge))

def _setup_eth(eth, bond):
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

def _setup_bridge(bridge, ip, netmask, gateway, resolver):
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

def _enable_ksm():
    '''
    Start KSM (Kernel Samepage Merging)

    http://www.linux-kvm.com/content/using-ksm-kernel-samepage-merging-kvm

    '''
    if (general.grep("/boot/config-" + os.uname()[2], "CONFIG_KSM=y")):
        general.shell_exec("service ksm start")
        general.shell_exec("chkconfig ksm on")

        general.shell_exec("service ksmtuned start")
        #general.shell_exec("service ksmtuned retune")
        general.shell_exec("chkconfig ksmtuned on")

def _abort_kvm_host_installation():
    '''
    Raise exception to abort the installation.

    '''
    raise Exception("Abort kvm host installation.")
