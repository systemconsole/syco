#!/usr/bin/env python
'''
Install the server to act as a KVM host.

Requirements:
    syco install-dhcp-server

    Installation of DHCP server due to a bug in the kickstarter, anaconda
    is always trying to get an ip from dhcp before settint the static ip.


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

from general import x, x_communicate
import app
import config
import disk
import general
import install
import iptables
import net
import netUtils
import version

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
        app.print_error("CPU doesn't support virtualization.")
        _abort_kvm_host_installation()

    if (not general.grep("/proc/cpuinfo", "constant_tsc")):
        app.print_error("CPU doesn't have a constant Time Stamp Counter.")
        _abort_kvm_host_installation()

    # Install the kvm packages
    install.package("qemu-kvm")
    install.package("libvirt")
    install.package("libguestfs-tools")
    install.package("avahi")

    # Provides the virt-install command for creating virtual machines.
    install.package("python-virtinst")

    # Before libvirtd starts, create a snapshot partion for qemu.
    _create_kvm_snapshot_partition()

    # Start services libvirtd depends on.
    x("service messagebus restart")
    x("service avahi-daemon start")
    x("chkconfig avahi-daemon on")

    # Start virsh
    x("service libvirtd start")

    _enable_ksm()

    # Looks like we need to wait for the libvirtd to start, otherwise
    # the virsh nodeinfo below doesn't work.
    time.sleep(1)

    # Set selinux
    x("setenforce 1")

    # Is virsh started?
    result = x("virsh nodeinfo")
    if "CPU model:" not in result:
        app.print_error("virsh not installed.")
        _abort_kvm_host_installation()

    result = x("virsh -c qemu:///system list")
    if "Id" not in result and "Name" not in result:
        app.print_error("virsh not installed.")
        _abort_kvm_host_installation()

    _remove_kvm_virt_networking()

    iptables.add_kvm_chain()
    iptables.save()

    version_obj.mark_executed()

    # Set selinux
    x("reboot")

    # Wait for the reboot to be executed, so the script
    # doesn't proceed to next command in install.cfg
    time.sleep(1000)

def _create_kvm_snapshot_partition():
    '''
    Create a partion that will be used by kvm/qemu to store guest snapshots.

    Memory snapshots when rebooting and such.

    TODO: Size should be equal to RAM.
    '''

    vol_group = "VolGroup00"
    disk.verify_volgroup(vol_group)
    devicename = "/dev/" + vol_group + "/qemu"
    result = x("lvdisplay -v " + devicename, output = False)
    if (devicename not in result):
        x("lvcreate -n qemu -L 100G " + vol_group)
        x("mkfs.ext4 -j " + devicename)
        x("mkdir -p /var/lib/libvirt/qemu")
        x("mount " + devicename + " /var/lib/libvirt/qemu")
        x("chown qemu:qemu /var/lib/libvirt/qemu")
        x("restorecon -R -v /var/lib/libvirt/qemu")

        # Automount the new partion when rebooting.
        value = devicename + "        /var/lib/libvirt/qemu     ext4        defaults                1 2"
        general.set_config_property("/etc/fstab", value, value)


def _remove_kvm_virt_networking():
    """
    Setup bonded network interfaces and bridges.

    """
    # Remove the virbr0, "NAT-interface".
    # http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Virtualization/chap-Virtualization-Network_Configuration.html
    x("virsh net-destroy default")
    x("virsh net-undefine default")
    x("service libvirtd restart")


def _enable_ksm():
    '''
    Start KSM (Kernel Samepage Merging)

    http://www.linux-kvm.com/content/using-ksm-kernel-samepage-merging-kvm

    '''
    if (general.grep("/boot/config-" + os.uname()[2], "CONFIG_KSM=y")):
        x("service ksm start")
        x("chkconfig ksm on")

        # 'ksmtuned start' gives a deadlock when using standard x and reading
        # on stdout.
        x_communicate("service ksmtuned start")
        #x("service ksmtuned retune")
        x("chkconfig ksmtuned on")

def _abort_kvm_host_installation():
    '''
    Raise exception to abort the installation.

    '''
    raise Exception("Abort kvm host installation.")
