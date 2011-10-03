#!/usr/bin/env python
'''
Install the server to act as a KVM host.

Read more:
http://www.linuxjournal.com/article/9764
http://www.redhat.com/promo/rhelonrhev/?intcmp=70160000000IUtyAAG
http://wiki.centos.org/HowTos/KVM
http://www.howtoforge.com/virtualization-with-kvm-on-a-fedora-11-server
http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/5/html-single/Virtualization/
http://www.cyberciti.biz/faq/centos-rhel-linux-kvm-virtulization-tutorial/

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os, re, time
import app, general, version, install
import net, iptables
import install
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
        return

    # Install the kvm packages
    install.package("qemu-kvm.x86_64")
    install.package("libvirt.x86_64")

    # Provides the virt-install command for creating virtual machines.
    install.package("python-virtinst")

    # Before libvirtd starts, create a snapshot partion for qemu.
    _create_kvm_snapshot_partition()

    # Start virsh
    general.shell_exec("service libvirtd start")

    # Looks like we need to wait for the libvirtd to start, otherwise
    # the virsh nodeinfo below doesn't work.
    time.sleep(1)

    # Set selinux
    general.shell_exec("setenforce 1")

    # Is virsh started?
    result = general.shell_exec("virsh nodeinfo")
    if "CPU model:                     x86_64" not in result:
        app.print_error("virsh not installed.")
        _abort_kvm_host_installation()
        return

    result = general.shell_exec("virsh -c qemu:///system list")
    if "Id Name" not in result:
        app.print_error("virsh not installed.")
        _abort_kvm_host_installation()
        return

    # todo: Might fix mouse problems in the host when viewing through VNC.
    # export SDL_VIDEO_X11_DGAMOUSE=0

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
    volgroup = _get_volgroup_name()
    devicename = "/dev/" + volgroup + "/qemu"
    result = general.shell_exec("lvdisplay -v " + devicename, output = False)
    if (devicename not in result):
        general.shell_exec("lvcreate -n qemu -L 100G " + volgroup)
        general.shell_exec("mkfs.ext4 -j " + devicename)
        general.shell_exec("mkdir -p /var/lib/libvirt/qemu")
        general.shell_exec("mount " + devicename + " /var/lib/libvirt/qemu")
        general.shell_exec("chcon -R system_u:object_r:qemu_var_run_t:s0 /var/lib/libvirt/qemu")
        general.shell_exec("chown qemu:qemu /var/lib/libvirt/qemu")

        # Automount the new partion when rebooting.
        value = devicename + "        /var/lib/libvirt/qemu     ext4        defaults                1 2"
        general.set_config_property("/etc/fstab", value, value)

def _get_volgroup_name():
    result = general.shell_exec("vgdisplay --activevolumegroups -c")
    volgroup = result.split(':', 1)[0].strip()

    if (not volgroup):
        raise Exception("Can't find any volgroup name")

    return volgroup

def _setup_network_interfaces():
    """
    Setup bonded network interfaces and bridges.

    Read more.
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
    front_ip = app.get_front_ip(net.get_hostname())
    back_ip = app.get_back_ip(net.get_hostname())
    front_gw = app.get_front_gateway_server_ip()
    back_gw = app.get_back_gateway_server_ip()
    if (num_of_if >= 4):
        # Setup front-net
        _setup_bridge("br0", front_ip, front_gw)
        _setup_bond("bond0", "br0")
        _setup_eth("eth0", "bond0")
        _setup_eth("eth1", "bond0")

        # _setup back-net
        _setup_bridge("br1", back_ip, back_gw)
        _setup_bond("bond1", "br1")
        _setup_eth("eth2", "bond1")
        _setup_eth("eth3", "bond1")
    elif (num_of_if == 2):
        # Setup front-net
        _setup_bridge("br0", front_ip, front_gw)
        _setup_bond("bond0", "br0")
        _setup_eth("eth0", "bond0")

        # _setup back-net
        _setup_bridge("br1", back_ip, back_gw)
        _setup_bond("bond1", "br1")
        _setup_eth("eth1", "bond1")
    else:
        raise(Exception("To few network interfaces: " + num_of_if))

def _setup_bond(bond, bridge):
    """
    Setup a bondX device.

    Will use mode: active-backup or 1
    - Sets an active-backup policy for fault tolerance. Transmissions are
    received and sent out via the first available bonded slave interface.
    Another bonded slave interface is only used if the active bonded slave
    interface fails.

    """
    _store_file("/etc/sysconfig/network-scripts/ifcfg-" + bond, """
DEVICE=%s
BONDING_OPTS="miimon=100 mode=1"
ONPARENT=yes
BOOTPROTO=none
#USERCTL=no
BRIDGE=br1
""" % (bond, bridge))

def _setup_eth(eth, bond):
    filename = "/etc/sysconfig/network-scripts/ifcfg-" + eth
    mac = _get_config_value(filename, "HWADDR")
    _store_file(filename, """
DEVICE=%s
HWADDR=%s
BOOTPROTO=none
ONBOOT=yes
MASTER=%s
SLAVE=yes
USERCTL=no
""" % (eth, mac, bond))

def _setup_bridge(bridge, ip, gateway):
    _store_file("/etc/sysconfig/network-scripts/ifcfg-" + bridge, """
DEVICE=%s
TYPE=Bridge
BOOTPROTO=static
ONBOOT=yes
IPADDR=%s
NETMASK=255.255.0.0
GATEWAY=%s
DNS1=%s
DNS2=8.8.8.8
""" % (bridge, ip, gateway, app.config.ger_first_dns_resolver()))

def _get_config_value(file_name, config_name):
    '''
    Get a value from an option in a config file.
    '''
    prog = re.compile("[\s]*" + config_name + "[:=\s]*(.*)")
    for line in open(file_name):
        m = prog.search(line)
        if m:
            return m.group(1)
    return False

def _store_file(file_name, value):
    '''
    Store a text in a file.
    '''
    app.print_verbose("storing file " + file_name)
    FILE = open(file_name, "w")
    FILE.writelines(value)
    FILE.close()

def _abort_kvm_host_installation():
    '''
    Write error message for aborting the installation.
    '''
    app.print_error("abort kvm host installation")
