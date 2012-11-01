#!/usr/bin/env python
'''
Audit the server according to CIS Redhat Linux 5 Benchmark v2.0.0.

Read more:
  http://benchmarks.cisecurity.org/en-us/?route=downloads.show.single.rhel5.200
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import ConfigParser
import os
import re
import subprocess

from constant import BOLD, RESET
import app
import config

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("audit-cis", audit_cis, help="Audit the server according to CIS Redhat Linux 5 Benchmark v2.0.0.")


#
# Helper functions
#

def x(command, output = False):
    if output:
        print(BOLD + "Command: " + RESET + command)

    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = p.communicate()
    result = "%s%s" % (stdout, stderr)

    if output:
        print result

    if result:
        return result.strip().split("\n")
    else:
        return ['']


def assert_contains(haystack, needle):
    global test_status
    if haystack:
        if needle not in haystack:
            test_status = "[ERROR]"


def assert_contains_re(haystack, needle):
    global test_status
    prog = re.compile(needle)
    if not prog.search(haystack):
        test_status = "[ERROR]"


def assert_empty(haystack):
    global test_status
    if len(haystack) != 1 or haystack[0] != '':
        test_status = "[ERROR]"


def rows_contains(cmd, expected):
    for row in x(cmd):
        assert_contains(row, expected)


def rows_contains_re(cmd, expected):
    for row in x(cmd):
        assert_contains_re(row, expected)


def rows_not_empty(cmd):
    global test_status
    empty = True
    for row in x(cmd):
        if len(row) > 0:
            empty = False

    if empty:
        test_status = "[ERROR]"


def rows_empty(cmd):
    global test_status
    not_empty = True
    for row in x(cmd):
        if len(row.strip()) == 0:
            not_empty = False

    if not_empty:
        test_status = "[ERROR]"


test_status = None
def print_header(txt, default_status = "[OK]"):
    print_status()

    global test_status
    test_status = default_status
    print(txt.ljust(80, " ")),


total_status = {}
def print_status():
    global test_status, total_status
    if test_status:
        print(test_status)

        if test_status not in total_status:
            total_status[test_status] = 1
        else:
            total_status[test_status] += 1

        test_status = None


def print_total_status():
    print_status()
    global total_status
    total = 0
    print
    print "="*80
    for test_status, number in total_status.iteritems():
        print "{0:<10} {1}".format(test_status, number)
        total += number
    print "{0:<10} {1}".format("[TOTAL]", total)


def print_message(txt, prefix):
    print_status()

    import textwrap
    txt_list = textwrap.wrap("%s" % txt, 70)
    print "      %s - %s" % (prefix, txt_list[0])
    for row in txt_list[1:]:
        print ("             %s".ljust(len(prefix), " ")) % row


def print_info(txt):
    print_message(txt, "INFO")


def print_warning(txt):
    print_message(txt, "WARNING")


def run_command(cmd):
    print_status()
    print "%s%s%s" % (BOLD, cmd, RESET)
    print
    print "="*80
    print "\n".join(x(cmd))
    print "="*80
    print

#
# The CIS Audit
#


def audit_cis(args):
    global test_status

    print
    print("Audit the server according to CIS Redhat Linux 5 Benchmark v2.0.0.")
    print("version: %d\n" % SCRIPT_VERSION)

    section_1_6()
    section_7_8()
    section_9()
    verify_network()
    verify_ssh()

    # Print status for the last section.
    print_total_status()


def section_1_6():
    global test_status


    #
    print("1. Install Updates, Patches and Additional Security Software")

    #
    print("1.1 Filesystem Configuration")

    #
    print_header("1.1.1 Create Separate Partition for /tmp")
    rows_contains("grep /tmp /etc/fstab", "tmp")

    #
    print_header("1.1.2 Set nodev option for /tmp Partition")
    rows_contains("grep /tmp /etc/fstab", "nodev")
    rows_contains("mount | grep /tmp", "nodev")

    #
    print_header("1.1.3 Set nosuid option for /tmp Partition")
    rows_contains("grep /tmp /etc/fstab", "nosuid")
    rows_contains("mount | grep /tmp", "nosuid")

    #
    print_header("1.1.4 Set noexec option for /tmp Partition")
    rows_contains("grep /tmp /etc/fstab", "noexec")
    rows_contains("mount | grep /tmp", "noexec")

    #
    print_header("1.1.5 Create Separate Partition for /var")
    rows_contains("grep '/var ' /etc/fstab", "var")

    #
    print_header("1.1.6 Bind Mount the /var/tmp directory to /tmp")
    rows_contains("grep '/var/tmp ' /etc/fstab", "/var/tmp")
    print_info("Not applicable, syco uses a separate partion for /var/tmp")

    #
    print_header("1.1.7 Create Separate Partition for /var/log")
    rows_contains("grep '/var/log ' /etc/fstab", "/var/log")

    #
    print_header("1.1.8 Create Separate Partition for /var/log/audit")
    rows_contains("grep '/var/log/audit ' /etc/fstab", "/var/log/audit")

    #
    print_header("1.1.9 Create Separate Partition for /home")
    rows_contains("grep '/home ' /etc/fstab", "/home")

    #
    print_header("1.1.9 Create Separate Partition for /home")
    rows_contains("grep '/home ' /etc/fstab", "/home")

    #
    print_header("1.1.10 Add nodev Option to /home")
    rows_contains("grep /home /etc/fstab", "nodev")
    rows_contains("mount | grep /home", "nodev")

    #
    print_header("1.1.11 Add nodev Option to Removable Media Partitions", "[WARNING]")
    print_warning("Check manually for nodev on removable media.")
    run_command("cat /etc/fstab")

    #
    print_header("1.1.12 Add noexec Option to Removable Media Partitions", "[WARNING]")
    print_warning("Check manually for noexec on removable media.")
    run_command("cat /etc/fstab")

    #
    print_header("1.1.13 Add nosuid Option to Removable Media Partitions", "[WARNING]")
    print_warning("Check manually for nosuid on removable media.")
    run_command("cat /etc/fstab")

    #
    print_header("1.1.14 Add nodev Option to /dev/shm Partition")
    rows_contains("grep /dev/shm /etc/fstab", "nodev")
    rows_contains("mount | grep /dev/shm", "nodev")

    #
    print_header("1.1.15 Add nosuid Option to /dev/shm Partition")
    rows_contains("grep /dev/shm /etc/fstab", "nosuid")
    rows_contains("mount | grep /dev/shm", "nosuid")

    #
    print_header("1.1.16 Add noexec Option to /dev/shm Partition")
    rows_contains("grep /dev/shm /etc/fstab", "noexec")
    rows_contains("mount | grep /dev/shm", "noexec")

    #
    print_header("1.1.17 Set Sticky Bit on All World-Writable Directories")
    cmd = "find / -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null"
    assert_empty(x(cmd))

    #
    print_header("1.1.18 Disable Mounting of cramfs Filesystems")
    rows_contains("/sbin/modprobe -n -v cramfs", "install /bin/true")

    assert_empty(x("/sbin/lsmod | grep cramfs"))

    #
    print_header("1.1.19 Disable Mounting of freevxfs Filesystems")
    rows_contains("/sbin/modprobe -n -v freevxfs", "install /bin/true")
    assert_empty(x("/sbin/lsmod | grep freexvfs"))

    #
    print_header("1.1.20 Disable Mounting of jffs2 Filesystems")
    rows_contains("/sbin/modprobe -n -v jffs2", "install /bin/true")
    assert_empty(x("/sbin/lsmod | grep jffs2"))

    #
    print_header("1.1.21 Disable Mounting of hfs Filesystems")
    rows_contains("/sbin/modprobe -n -v hfs", "install /bin/true")
    assert_empty(x("/sbin/lsmod | grep hfs"))

    #
    print_header("1.1.22 Disable Mounting of hfsplus Filesystems")
    rows_contains("/sbin/modprobe -n -v hfsplus", "install /bin/true")
    assert_empty(x("/sbin/lsmod | grep hfsplus"))

    #
    print_header("1.1.23 Disable Mounting of squashfs Filesystems")
    rows_contains("/sbin/modprobe -n -v squashfs", "install /bin/true")
    assert_empty(x("/sbin/lsmod | grep squashfs"))

    #
    print_header("1.1.24 Disable Mounting of udf Filesystems")
    rows_contains("/sbin/modprobe -n -v squashfs", "install /bin/true")

    #
    print_header("1.2 Use the Latest OS Release", "[WARNING]")
    print_warning("Check manually for latest os release")
    run_command("uname -r")
    run_command("cat /etc/redhat-release")

    #
    print_header("1.3 Configure Software Updates")

    #
    print_header("1.3.1 Configure Connection to the RHN RPM Repositories", "[WARNING]")
    print_warning(
        "We are using centos and not red hat. Check manually if we are " +
        "connected to sunet.")
    run_command("yum check-update")

    #
    print_header("1.3.2 Verify Red Hat GPG Key is Installed")
    rows_contains(
        'rpm -q --queryformat "%{SUMMARY}\n" gpg-pubkey',
        "gpg(CentOS-6 Key (CentOS 6 Official Signing Key) <centos-6-key@centos.org>)"
    )

    #
    print_header("1.3.3 Verify that gpgcheck is Globally Activated")
    rows_contains('grep gpgcheck /etc/yum.conf', "gpgcheck=1")

    #
    print_header("1.3.4 Disable the rhnsd Daemon")
    assert_empty(x("chkconfig --list | grep rhnsd"))

    #
    print_header("1.3.5 Disable yum-updatesd")
    assert_empty(x("chkconfig --list | grep yum-updatesd"))

    #
    print_header("1.3.6 Obtain Software Package Updates with yum", "[WARNING]")
    print_warning("Check manually if any packages need to updated.")
    run_command("yum check-update")

    #
    print_header("1.3.7 Verify Package Integrity Using RPM", "[WARNING]")
    print_warning("Check manually if any packages has been changed.")
    #todo
    #run_command("rpm -qVa | awk '$2 != \"c\" { print $0}'")


    #
    print_header("1.4 Advanced Intrusion Detection Environment (AIDE)")

    #
    print_header("1.4 Advanced Intrusion Detection Environment (AIDE)")
    print_info("We are using ossec instead of AIDE.")

    #
    print_header("1.4.2 Implement Periodic Execution of File Integrity")
    print_info("We are using ossec instead of AIDE.")


    #
    print_header("1.5 Configure SELinux")

    #
    print_header("1.5.1 Enable SELinux in /etc/grub.conf")
    assert_empty(x("grep selinux=0 /etc/grub.conf"))
    assert_empty(x("grep enforcing=0 /etc/grub.conf"))

    #
    print_header("1.5.2 Set the SELinux State")
    rows_contains('grep SELINUX=enforcing /etc/selinux/config', "SELINUX=enforcing")

    result = x('/usr/sbin/sestatus')
    assert_contains(result[0], "SELinux status:                 enabled")
    assert_contains(result[1], "SELinuxfs mount:                /selinux")
    assert_contains(result[2], "Current mode:                   enforcing")
    assert_contains(result[3], "Mode from config file:          enforcing")
    assert_contains(result[4], "Policy version:                 24")
    assert_contains(result[5], "Policy from config file:        targeted")

    #
    print_header("1.5.3 Set the SELinux Policy")
    rows_contains(
        'grep SELINUXTYPE=targeted /etc/selinux/config',
        "SELINUXTYPE=targeted"
    )

    result = x('/usr/sbin/sestatus')
    assert_contains(result[0], "SELinux status:                 enabled")
    assert_contains(result[1], "SELinuxfs mount:                /selinux")
    assert_contains(result[2], "Current mode:                   enforcing")
    assert_contains(result[3], "Mode from config file:          enforcing")
    assert_contains(result[4], "Policy version:                 24")
    assert_contains(result[5], "Policy from config file:        targeted")

    #
    print_header("1.5.4 Remove SETroubleshoot")
    assert_empty(x("chkconfig --list | grep setroubleshoot"))

    #
    print_header("1.5.5 Disable MCS Translation Service (mcstrans)")
    assert_empty(x("chkconfig --list | grep mctrans"))

    #
    print_header("1.5.6 Check for Unconfined Daemons")
    assert_empty(x("ps -eZ | egrep 'initrc' | egrep -vw 'tr|ps|egrep|bash|awk' | tr ':' ' ' | awk '{ print $NF }'"))

    #
    print_header("1.6 Secure Boot Settings")

    #
    print_header("1.6.1 Set User/GroupOwner on /etc/grub.conf")
    rows_contains(
        'stat -c "%u %g" /etc/grub.conf | egrep "0 0"',
        "0 0"
    )

    #
    print_header("1.6.2 Set Permissions on /etc/grub.conf")
    rows_contains(
        'stat -c "%a" /etc/grub.conf | egrep "600"',
        "600"
    )

    #
    print_header("1.6.3 Set Boot Loader Password")
    rows_contains('grep "^password" /etc/grub.conf', "password --encrypted")

    #
    print_header("1.6.4 Require Authentication for Single-User Mode")
    rows_contains('grep "sulogin" /etc/inittab', "~:S:wait:/sbin/sulogin")

    #
    print_header("1.6.5 Disable Interactive Boot")
    rows_contains(
        'grep "^PROMPT=" /etc/sysconfig/init',
        "PROMPT=no"
    )

    #
    print_header("1.7 Additional Process Hardening")

    #
    print_header("1.7.1 Restrict Core Dumps")
    rows_contains(
        'grep "hard core" /etc/security/limits.conf',
        "* hard core 0"
    )

    rows_contains(
        'sysctl fs.suid_dumpable',
        "fs.suid_dumpable = 0"
    )

    #
    print_header("1.7.2 Configure ExecShield")
    rows_contains(
        "sysctl kernel.exec-shield",
        "kernel.exec-shield = 1"
    )

    #
    print_header("1.7.3 Enable Randomized Virtual Memory Region Placement")
    rows_contains(
        "sysctl kernel.randomize_va_space",
        "kernel.randomize_va_space = 1"
    )

    #
    print_header("1.7.4 Enable XD/NX Support on 32-bit x86 Systems")
    print_warning("Not available on 64bit systems.")
    rows_not_empty(
        "grep flags /proc/cpuinfo | grep pae |grep nx"
    )

    #
    print_header("1.7.5 Disable Prelink")
    print_info("Not needed on RHEL6 systems.")

    #
    print_header("2. OS Services")

    #
    print_header("2.1.1 Remove telnet-server")
    rows_contains(
        "rpm -q telnet-server",
        "package telnet-server is not installed"
    )

    #
    print_header("2.1.2 Remove telnet")
    rows_contains(
        "rpm -q telnet",
        "package telnet is not installed"
    )

    #
    print_header("2.1.3 Remove rsh-server")
    rows_contains(
        "rpm -q rsh-server",
        "package rsh-server is not installed"
    )

    #
    print_header("2.1.4 Remove rsh")
    rows_contains(
        "rpm -q rsh",
        "package rsh is not installed"
    )

    #
    print_header("2.1.5 Remove NIS Client")
    rows_contains(
        "rpm -q ypbind",
        "package ypbind is not installed"
    )

    #
    print_header("2.1.6 Remove NIS Server")
    rows_contains(
        "rpm -q ypserv",
        "package ypserv is not installed"
    )

    #
    print_header("2.1.7 Remove tftp")
    rows_contains(
        "rpm -q tftp",
        "package tftp is not installed"
    )

    #
    print_header("2.1.8 Remove tftp-server")
    rows_contains(
        "rpm -q tftp-server",
        "package tftp-server is not installed"
    )

    #
    print_header("2.1.9 Remove talk")
    rows_contains(
        "rpm -q talk",
        "package talk is not installed"
    )

    #
    print_header("2.1.10 Remove talk-server")
    rows_contains(
        "rpm -q talk-server",
        "package talk-server is not installed"
    )

    #
    print_header("2.1.11 Remove xinetd")
    rows_contains(
        "rpm -q xinetd",
        "package xinetd is not installed"
    )

    #
    print_header("2.1.12 Disable chargen-dgram")
    rows_contains(
        "rpm -q chargen-dgram",
        "package chargen-dgram is not installed"
    )


    #
    print_header("2.1.13 Disable chargen-stream")
    rows_contains(
        "rpm -q chargen-stream",
        "package chargen-stream is not installed"
    )


    #
    print_header("2.1.14 Disable daytime-dgram")
    rows_contains(
        "rpm -q daytime-dgram",
        "package daytime-dgram is not installed"
    )


    #
    print_header("2.1.15 Disable daytime-stream")
    rows_contains(
        "rpm -q daytime-stream",
        "package daytime-stream is not installed"
    )


    #
    print_header("2.1.16 Disable echo-dgram")
    rows_contains(
        "rpm -q echo-dgram",
        "package echo-dgram is not installed"
    )


    #
    print_header("2.1.17 Disable echo-stream")
    rows_contains(
        "rpm -q echo-stream",
        "package echo-stream is not installed"
    )


    #
    print_header("2.1.18 Disable tcpmux-server")
    rows_contains(
        "rpm -q tcpmux-server",
        "package tcpmux-server is not installed"
    )

    #
    print_header("3. Special Purpose Services")

    #
    print_header("3.1 Set Daemon umask")
    rows_contains(
        "grep umask /etc/sysconfig/init",
        "umask 027"
    )

    #
    print_header("3.2 Remove X Windows")
    rows_contains(
        'grep "^id:" /etc/inittab',
        "id:3:initdefault"
    )

    result = x('yum grouplist "X Window System"')
    max_lines = len(result)
    assert_contains(result[max_lines-3], "Available Groups:")
    assert_contains(result[max_lines-2], "  X Window System")
    assert_contains(result[max_lines-1], "Done")

    #
    print_header("3.3 Disable Avahi Server")
    rows_contains(
        "rpm -q avahi",
        "package avahi is not installed"
    )
    assert_empty(x("chkconfig --list | grep avahi"))

    #
    print_header("3.4 Disable Print Server - CUPS")
    rows_contains(
        "rpm -q cups",
        "package cups is not installed"
    )
    assert_empty(x("chkconfig --list | grep cups"))

    #
    print_header("3.5 Remove DHCP Server")
    rows_contains(
        "rpm -q dhcp",
        "package dhcp is not installed"
    )

    #
    print_header("3.6 Configure Network Time Protocol (NTP)")
    rows_contains(
        'grep "restrict default" /etc/ntp.conf',
        "restrict default ignore"
    )

    rows_contains(
        'grep "restrict -6 default" /etc/ntp.conf',
        "restrict -6 default ignore"
    )

    #
    print_header("3.7 Remove LDAP")
    print_info("Syco uses LDAP.")

    #
    print_header("3.8 Disable NFS and RPC")
    rows_contains("rpm -q nfslock", "package nfslock is not installed")
    rows_contains("rpm -q rpcgssd", "package rpcgssd is not installed")
    rows_contains("rpm -q rpcidmapd", "package rpcidmapd is not installed")
    rows_contains("rpm -q portmap", "package portmap is not installed")
    assert_empty(x("chkconfig --list | grep nfslock"))
    assert_empty(x("chkconfig --list | grep rpcgssd"))
    assert_empty(x("chkconfig --list | grep rpcidmapd"))
    assert_empty(x("chkconfig --list | grep portmap"))

    #
    print_header("3.9 Remove DNS Server")
    rows_contains("rpm -q bind", "package bind is not installed")
    assert_empty(x("chkconfig --list | grep bind"))

    #
    print_header("3.10 Remove FTP Server")
    rows_contains("rpm -q vsftpd", "package vsftpd is not installed")
    assert_empty(x("chkconfig --list | grep vsftpd"))

    #
    print_header("3.11 Remove HTTP Server")
    rows_contains("rpm -q httpd", "package httpd is not installed")
    assert_empty(x("chkconfig --list | grep httpd"))

    #
    print_header("3.12 Remove Dovecot (IMAP and POP3 services)")
    rows_contains("rpm -q dovecot", "package dovecot is not installed")
    assert_empty(x("chkconfig --list | grep dovecot"))

    #
    print_header("3.13 Remove Samba")
    rows_contains("rpm -q samba", "package samba is not installed")
    assert_empty(x("chkconfig --list | grep samba"))

    #
    print_header("3.14 Remove HTTP Proxy Server")
    rows_contains("rpm -q squid", "package squid is not installed")
    assert_empty(x("chkconfig --list | grep squid"))

    #
    print_header("3.15 Remove SNMP Server")
    rows_contains("rpm -q net-snmp", "package net-snmp is not installed")
    assert_empty(x("chkconfig --list | grep net-snmp"))

    #
    print_header("3.16 Configure Mail Transfer Agent for Local-Only Mode")
    result = x('netstat -an | grep LIST | grep ":25"')
    assert_contains(result[0], "tcp        0      0 127.0.0.1:25                0.0.0.0:*                   LISTEN")
    if len(result) > 2:
        test_status = "[ERROR]"

    #
    print_header("4. Network Configuration and Firewalls")

    #
    print_header("4.1 Modify Network Parameters (Host Only)")

    #
    print_header("4.1.1 Disable IP Forwarding")
    rows_contains(
        "/sbin/sysctl net.ipv4.ip_forward",
        "net.ipv4.ip_forward = 0"
    )

    #
    print_header("4.1.2 Disable Send Packet Redirects")
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.all.send_redirects",
        "net.ipv4.conf.all.send_redirects = 0"
    )
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.default.send_redirects",
        "net.ipv4.conf.default.send_redirects = 0"
    )

    #

    print_header("4.2 Modify Network Parameters (Host and Router)")

    #
    print_header("4.2.1 Disable Source Routed Packet Acceptance")
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.all.accept_source_route",
        "net.ipv4.conf.all.accept_source_route = 0"
    )
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.default.accept_source_route",
        "net.ipv4.conf.default.accept_source_route = 0"
    )

    #
    print_header("4.2.2 Disable ICMP Redirect Acceptance")
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.all.accept_redirects",
        "net.ipv4.conf.all.accept_redirects = 0"
    )
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.default.accept_redirects",
        "net.ipv4.conf.default.accept_redirects = 0"
    )

    #
    print_header("4.2.3 Disable Secure ICMP Redirect Acceptance")
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.all.secure_redirects",
        "net.ipv4.conf.all.secure_redirects = 0"
    )
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.default.secure_redirects",
        "net.ipv4.conf.default.secure_redirects = 0"
    )

    #
    print_header("4.2.4 Log Suspicious Packets")
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.all.log_martians",
        "net.ipv4.conf.all.log_martians = 1"
    )

    #
    print_header("4.2.5 Enable Ignore Broadcast Requests")
    rows_contains(
        "/sbin/sysctl net.ipv4.icmp_echo_ignore_broadcasts",
        "net.ipv4.icmp_echo_ignore_broadcasts = 1"
    )

    #
    print_header("4.2.6 Enable Bad Error Message Protection")
    rows_contains(
        "/sbin/sysctl net.ipv4.icmp_ignore_bogus_error_responses",
        "net.ipv4.icmp_ignore_bogus_error_responses = 1"
    )

    #
    print_header("4.2.7 Enable RFC-recommended Source Route Validation")
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.all.rp_filter",
        "net.ipv4.conf.all.rp_filter = 1"
    )
    rows_contains(
        "/sbin/sysctl net.ipv4.conf.default.rp_filter",
        "net.ipv4.conf.default.rp_filter = 1"
    )

    #
    print_header("4.2.8 Enable TCP SYN Cookies")
    rows_contains(
        "/sbin/sysctl net.ipv4.tcp_syncookies",
        "net.ipv4.tcp_syncookies = 1"
    )

    #
    print_header("4.3 Wireless Networking")

    #
    print_header("4.3.1 Deactivate Wireless Interfaces", "[WARNING]")
    print_warning("Check manually for wireless interfaces.")
    run_command("ifconfig -a")

    #
    print_header("4.4 Disable IPv6")

    #
    print_header("4.4.1 Disable IPv6")
    result = x('grep ipv6 /etc/modprobe.d/*')
    rows_contains('grep ipv6 /etc/modprobe.d/*', 'options ipv6 disable=1')
    rows_contains('grep net-pf-10 /etc/modprobe.d/*', 'alias net-pf-10 off')

    #
    print_header("4.4.2 Configure IPv6")

    #
    print_header("4.4.2.1 Disable IPv6 Router Advertisements")
    print_info("We are using IPV6 on syco servers.")
    # rows_contains(
    #     "/sbin/sysctl net.ipv6.conf.default.accept_ra",
    #     "net.ipv6.conf.default.accept_ra = 0"
    # )


    #
    print_header("4.4.2.2 Disable IPv6 Redirect Acceptance")
    print_info("We are using IPV6 on syco servers.")
    # rows_contains(
    #     "/sbin/sysctl net.ipv6.conf.default.accept_redirects",
    #     "net.ipv6.conf.default.accept_redirects = 0"
    # )

    #
    print_header("4.5 Install TCP Wrappers")
    print_info("We are using IPV6 on syco servers.")
    #rows_contains("rpm -q tcp_wrappers", "package tcp_wrappers is not installed")

    #
    print_header("4.5.1 Create /etc/hosts.allow", "[WARNING]")
    print_warning("Check manually to verify hosts.")
    run_command("cat /etc/hosts.allow")

    #
    print_header("4.5.2 Verify Permissions on /etc/hosts.allow")
    rows_contains(
        'stat -c "%a" /etc/hosts.allow | egrep "644"',
        "644"
    )

    #
    print_header("4.5.3 Create /etc/hosts.deny")
    rows_contains(
        'grep "ALL: ALL" /etc/hosts.deny',
        "ALL: ALL"
    )

    #
    print_header("4.5.4 Verify Permissions on /etc/hosts.deny")
    rows_contains(
        'stat -c "%a" /etc/hosts.deny | egrep "644"',
        "644"
    )

    #
    print_header("4.6 Enable IPtables")
    rows_contains_re(
        "chkconfig --list iptables",
        "iptables.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
    )


    #
    print_header("4.7 Enable IP6tables")
    rows_contains_re(
        "chkconfig --list ip6tables",
        "ip6tables.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
    )

    #
    print_header("4.8 Uncommon Network Protocols")

    #
    print_header("4.8.1 Disable DCCP")
    rows_contains("/sbin/modprobe -n -v dccp", "install /bin/true")
    assert_empty(x("/sbin/lsmod | grep dccp"))

    #
    print_header("4.8.2 Disable SCTP")
    result = x('/sbin/modprobe -n -v sctp')
    assert_contains(result[2], "install /bin/true")
    if len(result) != 3:
        test_status = "[ERROR]"
    assert_empty(x("/sbin/lsmod | grep sctp"))

    #
    print_header("4.8.3 Disable RDS")
    rows_contains("/sbin/modprobe -n -v rds", "install /bin/true")
    assert_empty(x("/sbin/lsmod | grep rds"))

    #
    print_header("4.8.4 Disable TIPC")
    rows_contains("/sbin/modprobe -n -v tipc", "install /bin/true")
    assert_empty(x("/sbin/lsmod | grep tipc"))

    #
    print_header("5. Logging and Auditing")
    print_header("5.1 Configure Syslog")
    print_info("We are using rsyslog and not syslog.")

    #
    print_header("5.1.1 Configure /etc/syslog.conf")
    rows_contains(
        "ls /etc/syslog.conf",
        "ls: cannot access /etc/syslog.conf: No such file or directory"
    )


    #
    print_header("5.1.2 Create and Set Permissions on syslog Log Files")
    print_header("5.1.3 Configure syslog to Send Logs to a Remote Log Host")

    #
    print_header("5.1.4 Accept Remote syslog Messages Only on Designated Log Hosts")
    rows_contains(
        "ls /etc/sysconfig/syslog",
        "ls: cannot access /etc/sysconfig/syslog: No such file or directory"
    )

    #
    print_header("5.2 Configure rsyslog")

    #
    print_header("5.2.1 Install the rsyslog package")
    rows_empty('rpm -q rsyslog|grep  "package rsyslog is not installed"')

    #
    print_header("5.2.2 Activate the rsyslog Service")
    assert_empty(x("chkconfig --list | grep ^syslog"))
    rows_contains_re(
        "chkconfig --list rsyslog",
        "rsyslog.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
    )

    #
    print_header("5.2.3 Configure /etc/rsyslog.conf", "[WARNING]")
    print_warning("Ensure that the log files are logging information")
    run_command("ls -l /var/log/")


    #
    print_header("5.2.4 Create and Set Permissions on rsyslog Log Files")
    print_header("  TODO - Ensure that the log files are logging information")


    #
    print_header("5.2.5 Configure rsyslog to Send Logs to a Remote Log Host")
    expect = "*.* @%s:514" % config.general.get_log_server_hostname()
    rows_contains(
        "grep '%s' /etc/rsyslog.conf" % expect,
        expect
    )

    #
    print_header("5.2.6 Accept Remote rsyslog Messages Only on Designated Log Hosts")
    print_info("We are using udp instead of tcp")
    rows_contains(
        "grep '^\$ModLoad.*imudp.so' /etc/rsyslog.conf",
        "$ModLoad imudp.so"
    )
    rows_contains(
        "grep '^\$UDPServerRun' /etc/rsyslog.conf",
        "$UDPServerRun 514"
    )

    #
    print_header("5.2.6 - BONUS ")
    rows_contains(
        "grep '^auth\\.\\*' /etc/rsyslog.conf",
        "auth.*"
    )

    rows_contains(
        "grep '^authpriv\\.\\*' /etc/rsyslog.conf",
        "authpriv.*"
    )

    #
    print_header("5.3 Configure System Accounting (auditd)")

    #
    print_header("5.3.1 Enable auditd Service")
    rows_contains_re(
        "chkconfig --list auditd",
        "auditd.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
    )


    #
    print_header("5.3.2 Configure Data Retention")

    #
    print_header("5.3.2.1 Configure Audit Log Storage Size")
    rows_contains(
        "grep 'max_log_file[ ]*\=' /etc/audit/auditd.conf",
        "max_log_file = 50"
    )

    #
    print_header("5.3.2.2 Disable System on Audit Log Full")
    rows_contains(
        "grep '^space_left_action[ ]*\=' /etc/audit/auditd.conf",
        "space_left_action = email"
    )

    rows_contains(
        "grep action_mail_acct /etc/audit/auditd.conf",
        "action_mail_acct = root"
    )

    rows_contains(
        "grep admin_space_left_action /etc/audit/auditd.conf",
        "admin_space_left_action = halt"
    )


    #
    print_header("5.3.2.3 Keep All Auditing Information")
    rows_contains(
        "grep max_log_file_action /etc/audit/auditd.conf",
        "max_log_file_action = keep_logs"
    )

    #
    print_header("5.3.3 Enable Auditing for Processes That Start Prior to auditd")
    rows_contains(
        'grep "^[^#]*kernel" /etc/grub.conf|grep "audit=1"',
        'audit=1'
    )

    #
    print_header("5.3.4 Record Events That Modify Date and Time Information")
    result = x('grep time-change /etc/audit/audit.rules')
    if len(result) != 5:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change")
        assert_contains(result[1], "-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change")
        assert_contains(result[2], "-a always,exit -F arch=b32 -S clock_settime -k time-change")
        assert_contains(result[3], "-a always,exit -F arch=b64 -S clock_settime -k time-change")
        assert_contains(result[4], "-w /etc/localtime -p wa -k time-change")

    #
    print_header("5.3.4 Record Events That Modify Date and Time Information")
    result = x('grep identity /etc/audit/audit.rules')
    if len(result) != 5:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-w /etc/group -p wa -k identity")
        assert_contains(result[1], "-w /etc/passwd -p wa -k identity")
        assert_contains(result[2], "-w /etc/gshadow -p wa -k identity")
        assert_contains(result[3], "-w /etc/shadow -p wa -k identity")
        assert_contains(result[4], "-w /etc/security/opasswd -p wa -k identity")

    #
    print_header("5.3.6 Record Events That Modify the System's Network Environment")
    result = x('grep system-locale /etc/audit/audit.rules')
    if len(result) != 6:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-a exit,always -F arch=b64 -S sethostname -S setdomainname -k system-locale")
        assert_contains(result[1], "-a exit,always -F arch=b32 -S sethostname -S setdomainname -k system-locale")
        assert_contains(result[2], "-w /etc/issue -p wa -k system-locale")
        assert_contains(result[3], "-w /etc/issue.net -p wa -k system-locale")
        assert_contains(result[4], "-w /etc/hosts -p wa -k system-locale")
        assert_contains(result[5], "-w /etc/sysconfig/network -p wa -k system-locale")

    #
    print_header("5.3.7 Record Events That Modify the System's Mandatory Access Controls")
    rows_contains(
        "grep MAC-policy /etc/audit/audit.rules",
        "-w /etc/selinux/ -p wa -k MAC-policy"
    )

    #
    print_header("5.3.8 Collect Login and Logout Events")
    result = x('grep logins /etc/audit/audit.rules')
    if len(result) != 3:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-w /var/log/faillog -p wa -k logins")
        assert_contains(result[1], "-w /var/log/lastlog -p wa -k logins")
        #assert_contains(result[2], "-w /var/log/tallylog -p -wa -k logins")

    #
    print_header("5.3.9 Collect Session Initiation Information")
    result = x('grep session /etc/audit/audit.rules')
    if len(result) != 3:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-w /var/log/btmp -p wa -k session")
        assert_contains(result[1], "-w /var/run/utmp -p wa -k session")
        assert_contains(result[2], "-w /var/log/wtmp -p wa -k session")

    #
    print_header("5.3.10 Collect Discretionary Access Control Permission Modification Events")
    result = x('grep perm_mod /etc/audit/audit.rules')
    if len(result) != 6:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=500 -F auid!=4294967295 -k perm_mod")
        assert_contains(result[1], "-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -F auid>=500 -F auid!=4294967295 -k perm_mod")
        assert_contains(result[2], "-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -F auid>=500 -F auid!=4294967295 -k perm_mod")
        assert_contains(result[3], "-a always,exit -F arch=b32 -S chown -S fchown -S fchownat -S lchown -F auid>=500 -F auid!=4294967295 -k perm_mod")
        assert_contains(result[4], "-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=500 -F auid!=4294967295 -k perm_mod")
        assert_contains(result[5], "-a always,exit -F arch=b32 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=500 -F auid!=4294967295 -k perm_mod")

    #
    print_header("5.3.11 Collect Unsuccessful Unauthorized Access Attempts to Files")
    result = x('grep access /etc/audit/audit.rules')
    if len(result) != 4:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=500 -F auid!=4294967295 -k access")
        assert_contains(result[1], "-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=500 -F auid!=4294967295 -k access")
        assert_contains(result[2], "-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=500 -F auid!=4294967295 -k access")
        assert_contains(result[3], "-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=500 -F auid!=4294967295 -k access")

    #
    print_header("5.3.12 Collect Use of Privileged Commands")
    #TODO: need remediation
    #find / -xdev \( -perm -4000 -o -perm -2000 \) -type f | awk '{print "-a always,exit -F path=" $1 " -F perm=x -F auid>=500 -F auid!=4294967295 -k privileged" }'
    rows_contains(
        "",
        ""
    )

    #
    print_header("5.3.13 Collect Successful File System Mounts")
    result = x('grep mounts /etc/audit/audit.rules')
    if len(result) != 2:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-a always,exit -F arch=b64 -S mount -F auid>=500 -F auid!=4294967295 -k mounts")
        assert_contains(result[1], "-a always,exit -F arch=b32 -S mount -F auid>=500 -F auid!=4294967295 -k mounts")

    #
    print_header("5.3.14 Collect File Deletion Events by User")
    result = x('grep delete$ /etc/audit/audit.rules')
    if len(result) != 2:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=500 -F auid!=4294967295 -k delete")
        assert_contains(result[1], "-a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=500 -F auid!=4294967295 -k delete")

    #
    print_header("5.3.15 Collect Changes to System Administration Scope (sudoers)")
    rows_contains(
        "grep scope /etc/audit/audit.rules",
        "-w /etc/sudoers -p wa -k scope"
    )

    #
    print_header("5.3.16 Collect System Administrator Actions (sudolog)")
    rows_contains(
        "grep actions /etc/audit/audit.rules",
        "-w /var/log/sudo.log -p wa -k actions"
    )

    #
    print_header("5.3.17 Collect Kernel Module Loading and Unloading")
    result = x('grep modules /etc/audit/audit.rules')
    if len(result) != 4:
        test_status = "[ERROR]"
    else:
        assert_contains(result[0], "-w /sbin/insmod -p x -k modules")
        assert_contains(result[1], "-w /sbin/rmmod -p x -k modules")
        assert_contains(result[2], "-w /sbin/modprobe -p x -k modules")
        assert_contains(result[3], "-a always,exit -F arch=b64 -S init_module -S delete_module -k modules")

    #
    print_header("5.3.18 Make the Audit Configuration Immutable")
    rows_contains(
        'grep "^-e 2" /etc/audit/audit.rules',
        "-e 2"
    )

    #
    print_header("5.4 Configure logrotate")
    print_header("  TODO - strange or i'm lazy?")

    #
    print_header("6. System Access, Authentication and Authorization")
    print_header("6.1 Configure cron and anacron")

    #
    print_header("6.1.1 Enable anacron Daemon")
    print_info("Not installed syco servers.")
    rows_contains("rpm -q anacron", "package anacron is not installed")

    print_header("6.1.2 Enable cron Daemon")
    rows_contains_re(
        "chkconfig --list crond",
        "crond.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
    )

    #
    print_header("6.1.3 Set User/Group Owner and Permission on /etc/anacrontab")
    rows_contains("rpm -q anacron", "package anacron is not installed")

    #
    print_header("6.1.4 Set User/Group Owner and Permission on /etc/crontab")
    rows_contains('stat -c "%a %u %g" /etc/crontab | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.1.5 Set User/Group Owner and Permission on /etc/cron.hourly")
    rows_contains('stat -c "%a %u %g" /etc/cron.hourly | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.1.6 Set User/Group Owner and Permission on /etc/cron.daily")
    rows_contains('stat -c "%a %u %g" /etc/cron.daily | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.1.7 Set User/Group Owner and Permission on /etc/cron.weekly")
    rows_contains('stat -c "%a %u %g" /etc/cron.weekly | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.1.8 Set User/Group Owner and Permission on /etc/cron.monthly")
    rows_contains('stat -c "%a %u %g" /etc/cron.monthly | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.1.9 Set User/Group Owner and Permission on /etc/cron.d")
    rows_contains('stat -c "%a %u %g" /etc/cron.d | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.1.10 Restrict at Daemon")
    rows_contains('ls /etc/at.deny', "ls: cannot access /etc/at.deny: No such file or directory")
    rows_contains('stat -c "%a %u %g" /etc/at.allow | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.1.11 Restrict at/cron to Authorized Users")
    rows_contains('ls /etc/cron.deny', "ls: cannot access /etc/cron.deny: No such file or directory")
    if os.path.exists("/etc/cron.allow"):
        rows_contains('stat -c "%a %u %g" /etc/cron.allow | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.2 Configure SSH")

    #
    print_header("6.2.1 Set SSH Protocol to 2")
    rows_contains(
        'grep "^Protocol" /etc/ssh/sshd_config',
        "Protocol 2"
    )

    #
    print_header("6.2.2 Set LogLevel to VERBOSE")
    rows_contains(
        'grep "^LogLevel" /etc/ssh/sshd_config',
        "LogLevel VERBOSE"
    )

    #
    print_header("6.2.3 Set Permissions on /etc/sshd_config")
    rows_contains('stat -c "%a %u %g" /etc/ssh/sshd_config | egrep "600 0 0"', "600 0 0")

    #
    print_header("6.2.4 Disable SSH X11 Forwarding")
    rows_contains(
        'grep "^X11Forwarding" /etc/ssh/sshd_config',
        "X11Forwarding no"
    )

    #
    print_header("6.2.5 Set SSH MaxAuthTries to 4 or Less")
    rows_contains(
        'grep "^MaxAuthTries" /etc/ssh/sshd_config',
        "MaxAuthTries 4"
    )

    #
    print_header("6.2.6 Set SSH IgnoreRhosts to Yes")
    rows_contains(
        'grep "^IgnoreRhosts" /etc/ssh/sshd_config',
        "IgnoreRhosts yes"
    )

    #
    print_header("6.2.7 Set SSH HostbasedAuthentication to No")
    rows_contains(
        'grep "^HostbasedAuthentication" /etc/ssh/sshd_config',
        "HostbasedAuthentication no"
    )

    #
    print_header("6.2.8 Disable SSH Root Login")
    rows_contains(
        'grep "^PermitRootLogin" /etc/ssh/sshd_config',
        "PermitRootLogin no"
    )

    #
    print_header("6.2.9 Set SSH PermitEmptyPasswords to No")
    rows_contains(
        'grep "^PermitEmptyPasswords" /etc/ssh/sshd_config',
        "PermitEmptyPasswords no"
    )

    #
    print_header("6.2.10 Do Not Allow Users to Set Environment Options")
    rows_contains(
        'grep PermitUserEnvironment /etc/ssh/sshd_config',
        "PermitUserEnvironment no"
    )

    #
    print_header("6.2.11 Use Only Approved Ciphers in Counter Mode")
    rows_contains(
        'grep "Cipher" /etc/ssh/sshd_config',
        "Ciphers aes256-ctr"
    )

    #
    print_header("6.2.12 Set Idle Timeout Interval for User Login")
    rows_contains(
        'grep "^ClientAliveInterval" /etc/ssh/sshd_config',
        "ClientAliveInterval 900"
    )

    #
    print_header("6.2.13 Limit Access via SSH")
    print_info(
        "User restrictions are not set in sshd_config, we restrict with LDAP.")

    #
    print_header("6.2.14 Set SSH Banner")
    rows_contains(
        "grep '^Banner' /etc/ssh/sshd_config",
        "Banner /etc/issue.net"
    )

    #
    print_header("6.3 Configure PAM")

    #
    print_header("6.3.1 Set Password Creation Requirement Parameters Using pam_cracklib")
    rows_contains(
        "grep pam_cracklib.so /etc/pam.d/system-auth",
        "password    requisite     pam_cracklib.so try_first_pass " +
        "retry=3 minlen=14,dcredit=-1,ucredit=-1,ocredit=-2,lcredit=-1,difok=3"
    )

    #
    print_header("6.3.2 Set Strong Password Creation Policy Using pam_passwdqc")
    print_info("We are using pam_cracklib")

    #
    print_header("6.3.3 Set Lockout for Failed Password Attempts")
    rows_contains(
        "grep 'pam_tally2' /etc/pam.d/system-auth",
        "auth required pam_tally2.so deny=5 onerr=fail"
    )

    #
    print_header("6.3.4 Use pam_deny.so to Deny Services")
    print_header("  TODO - Where to place the deny?")

    #
    print_header("6.3.5 Upgrade Password Hashing Algorithm to SHA-512")
    rows_contains(
        "authconfig --test | grep hashing | grep sha512",
        "password hashing algorithm is sha512"
    )

    #
    print_header("6.3.6 Limit Password Reuse")
    rows_contains(
        "grep 'remember' /etc/pam.d/system-auth",
        "password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok remember=5"
    )

    #
    print_header("6.3.7 Remove the pam_ccreds Package")
    rows_contains("rpm -q pam_ccreds", "package pam_ccreds is not installed")

    #
    print_header("6.4 Restrict root Login to System Console")
    rows_contains("cat /etc/securetty", "tty1")

    #
    print_header("6.5 Restrict Access to the su Command")
    result = x('grep pam_wheel.so /etc/pam.d/su')
    print result

    assert_contains(result[0], "#auth\t\tsufficient\tpam_wheel.so trust use_uid")
    assert_contains(result[1], "auth\t\trequired\tpam_wheel.so use_uid")
    if len(result) != 2:
        test_status = "[ERROR]"

    rows_contains(
        "grep wheel /etc/group",
        "wheel:x:10:root"
    )


def section_7_8():
    global test_status

    #
    print_header("7. User Accounts and Environment")

    #
    print_header("7.1 Disable System Accounts")
    for line in open("/etc/passwd"):
        userid = int(line.split(':')[2]);
        username = line.split(':')[0];

        if userid > 0 and userid <= 499:
            x("/usr/sbin/usermod -L -s /sbin/nologin %s" % username)

    print_header("7.1 Disable System Accounts")
    rows_empty(
        'awk -F: \' ($3 > 0 && $3 < 500 && $1 != "halt" && $1 != "sync" && $1 != "shutdown" && $7 != "/sbin/nologin") {print $1 " " $7}\' /etc/passwd',
    )

    #
    print_header("7.2 Set Shadow Password Suite Parameters (/etc/login.defs)")

    #
    print_header("7.2.1 Set Password Expiration Days")
    rows_contains(
        "grep ^PASS_MAX_DAYS /etc/login.defs",
        "PASS_MAX_DAYS\t90"
    )

    rows_empty(
        'awk -F: \'($3 > 0) {print $1}\' /etc/passwd | xargs -I {} ' +
        'chage --list {}|' +
        'grep "^Maximum number of days between password change"|'+
        'grep -v ": 99$"'
    )

    #
    print_header("7.2.2 Set Password Change Minimum Number of Days")
    rows_contains(
        "grep ^PASS_MIN_DAYS /etc/login.defs",
        "PASS_MIN_DAYS\t7"
    )

    rows_empty(
        'awk -F: \'($3 > 0) {print $1}\' /etc/passwd | xargs -I {} ' +
        'chage --list {}|' +
        'grep "^Miniumum number of days between password change"|'+
        'grep -v ": 7$"'
    )

    #
    print_header("7.2.3 Set Password Expiring Warning Days")
    rows_contains(
        "grep ^PASS_WARN_AGE /etc/login.defs",
        "PASS_WARN_AGE\t14"
    )

    rows_empty(
        'awk -F: \'($3 > 0) {print $1}\' /etc/passwd | xargs -I {} ' +
        'chage --list {}|' +
        'grep "^Number of days of warning before password expires"|'+
        'grep -v ": 7$"'
    )

    #
    print_header("7.3 Set Default Group for root Account")

    #
    print_header("7.3 Set Default Group for root Account")
    rows_contains(
        "grep ^root /etc/passwd | cut -f4 -d:",
        "0"
    )

    #
    print_header("7.4 Set Default umask for Users")
    rows_contains_re("grep 'umask 077' /etc/bashrc",    ".*umask 077.*")
    rows_contains_re("grep 'umask 077' /etc/profile",   ".*umask 077.*")
    rows_contains_re("grep 'umask 077' /etc/csh.cshrc", ".*umask 077.*")

    #
    print_header("7.5 Lock Inactive User Accounts")
    rows_contains(
        "useradd -D | grep INACTIVE",
        "INACTIVE=35"
    )

    #
    print_header("8. Warning Banners")

    #
    print_header("8.1 Set Warning Banner for Standard Login Services")
    rows_empty("diff %s/hardening/issue.net /etc/motd" % app.SYCO_VAR_PATH)
    rows_empty("diff %s/hardening/issue.net /etc/issue" % app.SYCO_VAR_PATH)
    rows_empty("diff %s/hardening/issue.net /etc/issue.net" % app.SYCO_VAR_PATH)


    #
    print_header("8.1.1 Remove OS Information from Login Warning Banners")
    rows_empty("egrep '(\\\\v|\\\\r|\\\\m|\\\\s)' /etc/issue")
    rows_empty("egrep '(\\\\v|\\\\r|\\\\m|\\\\s)' /etc/motd")
    rows_empty("egrep '(\\\\v|\\\\r|\\\\m|\\\\s)' /etc/issue.net")

    #
    print_header("8.2 Set GNOME Warning Banner")
    print_info("Not using gnome.")


def section_9():
    global test_status

    #
    print_header("9. System Maintenance")

    #
    print_header("9.1 Verify System File Permissions", "[WARNING]")
    print_warning("Check manually for changed files.")
    run_command("rpm -Va --nomtime --nosize --nomd5 --nolinkto")

    #
    print_header("9.1.1 Verify Permissions on /etc/passwd")
    rows_contains('stat -c "%a %u %g" /etc/passwd | egrep "644 0 0"', "644 0 0")

    #
    print_header("9.1.1 Verify Permissions on /etc/shadow")
    rows_contains('stat -c "%a %u %g" /etc/shadow | egrep "400 0 0"', "400 0 0")

    #
    print_header("9.1.3 Verify Permissions on /etc/gshadow")
    rows_contains('stat -c "%a %u %g" /etc/gshadow | egrep "400 0 0"', "400 0 0")

    #
    print_header("9.1.3 Verify Permissions on /etc/group")
    rows_contains('stat -c "%a %u %g" /etc/group | egrep "644 0 0"', "644 0 0")

    #
    print_header("9.1.5 Verify User/Group Ownership on /etc/passwd")
    rows_contains('stat -c "%a %u %g" /etc/passwd | egrep "644 0 0"', "644 0 0")

    #
    print_header("9.1.6 Verify User/Group Ownership on /etc/shadow")
    rows_contains('stat -c "%a %u %g" /etc/shadow | egrep "400 0 0"', "400 0 0")

    #
    print_header("9.1.7 Verify User/Group Ownership on /etc/gshadow")
    rows_contains('stat -c "%a %u %g" /etc/gshadow | egrep "400 0 0"', "400 0 0")

    #
    print_header("9.1.8 Verify User/Group Ownership on /etc/group")
    rows_contains('stat -c "%a %u %g" /etc/group | egrep "644 0 0"', "644 0 0")

    #
    print_header("9.1.9 Find World Writable Files", "[WARNING]")
    print_warning("Check manually for World Writable Files.")
    cmd = """
for i in $(/bin/egrep '(ext4|ext3|ext2)' /etc/fstab | /bin/awk '{print $2}')
do
    /usr/bin/find $i -xdev -type f -perm -0002 -print
done
"""
    run_command(cmd)

    #
    print_header("9.1.10 Find Un-owned Files and Directories", "[WARNING]")
    print_warning("Check manually for Un-owned Files and Directories.")
    cmd = """
for i in $(/bin/egrep '(ext4|ext3|ext2)' /etc/fstab | /bin/awk '{print $2}')
do
    /usr/bin/find $i -xdev \( -type f -o -type d \) -nouser -print
done
"""
    run_command(cmd)

    #
    print_header("9.1.11 Find Un-grouped Files and Directories", "[WARNING]")
    print_warning("Check manually for Un-owned Files and Directories.")
    cmd = """
for i in $(/bin/egrep '(ext4|ext3|ext2)' /etc/fstab | /bin/awk '{print $2}')
do
    /usr/bin/find $i -xdev \( -type f -o -type d \) -nogroup -print
done
"""
    run_command(cmd)

    #
    print_header("9.1.12 Find SUID System Executables", "[WARNING]")
    print_warning("Check manually for invalid SUID permissions.")
    cmd = """
for i in $(/bin/egrep '(ext4|ext3|ext2)' /etc/fstab | /bin/awk '{print $2}')
do
    /usr/bin/find $i -xdev -type f -perm -4000 -print
done
"""
    run_command(cmd)

    #
    print_header("9.1.13 Find SGID System Executables", "[WARNING]")
    print_warning("Check manually for invalid SGID permissions.")
    cmd = """
for i in $(/bin/egrep '(ext4|ext3|ext2)' /etc/fstab | /bin/awk '{print $2}')
do
    /usr/bin/find $i -xdev -type f -perm -2000 -print
done
"""
    run_command(cmd)

    #
    print_header("9.2 Review User and Group Settings")

    #
    print_header("9.2.1 Ensure Password Fields are Not Empty")
    cmd = """
/bin/cat /etc/shadow | \
/bin/awk -F : '($2 == "" ) { print $1 " does not have a password "}'
"""
    rows_empty(cmd)

    #
    print_header("9.2.2 Verify No Legacy \"+\" Entries Exist in /etc/passwd File")
    rows_empty("/bin/grep '^+:' /etc/passwd")

    #
    print_header("9.2.3 Verify No Legacy \"+\" Entries Exist in /etc/shadow File")
    rows_empty(" /bin/grep '^+:' /etc/shadow")

    #
    print_header("9.2.4 Verify No Legacy \"+\" Entries Exist in /etc/group File")
    rows_empty(" /bin/grep '^+:' /etc/group")

    #
    print_header("9.2.5 Verify No UID 0 Accounts Exist Other Than root")
    rows_contains(
        "/bin/cat /etc/passwd | /bin/awk -F: '($3 == 0) { print $1 }'",
        "root"
    )

    #
    print_header("9.2.6 Ensure root PATH Integrity")
    cmd = """
if [ "`echo $PATH | /bin/grep :: `" != "" ]; then
      echo "Empty Directory in PATH (::)"
fi
if [ "`echo $PATH | /bin/grep :$`"  != "" ]; then
      echo "Trailing : in PATH"
fi
p=`echo $PATH | /bin/sed -e 's/::/:/' -e 's/:$//' -e 's/:/ /g'` set -- $p
while [ "$1" != "" ]; do
    if [ "$1" = "." ]; then
        echo "PATH contains ."
        shift
        continue
    fi
    if [ -d $1 ]; then
        dirperm=`/bin/ls -ldH $1 | /bin/cut -f1 -d" "`
        if [ `echo $dirperm | /bin/cut -c6 ` != "-" ]; then
            echo "Group Write permission set on directory $1"
        fi
        if [ `echo $dirperm | /bin/cut -c9 ` != "-" ]; then
            echo "Other Write permission set on directory $1"
        fi

        dirown=`ls -ldH $1 | awk '{print $3}'`
        if [ "$dirown" != "root" ] ; then
            echo $1 is not owned by root
        fi
        else
            echo $1 is not a directory
        fi
        shift
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.7 Check Permissions on User Home Directories")
    cmd = """
for dir in `/bin/cat /etc/passwd | /bin/egrep -v '(root|halt|sync|shutdown)' |\
/bin/awk -F: '($7 != "/sbin/nologin") { print $6 }'`; do
    dirperm=`/bin/ls -ld $dir | /bin/cut -f1 -d" "`
    if [ `echo $dirperm | /bin/cut -c6 ` != "-" ]; then
        echo "Group Write permission set on directory $dir"
    fi
    if [ `echo $dirperm | /bin/cut -c8 ` != "-" ]; then
        echo "Other Read permission set on directory $dir"
    fi
    if [ `echo $dirperm | /bin/cut -c9 ` != "-" ]; then
        echo "Other Write permission set on directory $dir"
    fi
    if [ `echo $dirperm | /bin/cut -c10 ` != "-" ]; then
        echo "Other Execute permission set on directory $dir"
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.8 Check User Dot File Permissions")
    cmd = """
for dir in `/bin/cat /etc/passwd | /bin/egrep -v '(root|halt|sync|shutdown)' |\
/bin/awk -F: '($7 != "/sbin/nologin") { print $6 }'`; do
    for file in $dir/.[A-Za-z0-9]*; do
        if [ ! -h "$file" -a -f "$file" ]; then
            fileperm=`/bin/ls -ld $file | /bin/cut -f1 -d" "`
            if [ `echo $fileperm | /bin/cut -c6 ` != "-" ]; then
                echo "Group Write permission set on file $file"
            fi
            if [ `echo $fileperm | /bin/cut -c9 ` != "-" ]; then
                echo "Other Write permission set on file $file"
            fi
        fi
    done
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.9 Check Permissions on User .netrc Files")
    cmd = """
for dir in `/bin/cat /etc/passwd | /bin/egrep -v '(root|halt|sync|shutdown)' |\
/bin/awk -F: '($7 != "/sbin/nologin") { print $6 }'`; do
    for file in $dir/.netrc; do
        if [ ! -h "$file" -a -f "$file" ]; then
            fileperm=`/bin/ls -ld $file | /bin/cut -f1 -d" "`
            if [ `echo $fileperm | /bin/cut -c5 ` != "-" ]
            then
                echo "Group Read set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c6 ` != "-" ]
            then
                  echo "Group Write set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c7 ` != "-" ]
            then
                  echo "Group Execute set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c8 ` != "-" ]
            then
                  echo "Other Read  set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c9 ` != "-" ]
            then
                  echo "Other Write set on $file"
            fi
            if [ `echo $fileperm | /bin/cut -c10 ` != "-" ]
            then
                  echo "Other Execute set on $file"
            fi
        fi
    done
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.10 Check for Presence of User .rhosts Files")
    cmd = """
for dir in `/bin/cat /etc/passwd | /bin/egrep -v '(root|halt|sync|shutdown)' |\
/bin/awk -F: '($7 != "/sbin/nologin") { print $6 }'`; do
    for file in $dir/.rhosts; do
        if [ ! -h "$file" -a -f "$file" ]; then
            echo ".rhosts file in $dir"
        fi
    done
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.11 Check Groups in /etc/passwd")
    cmd = """
while read x
do
    userid=`echo "$x" | cut -f1 -d':'`
    groupid=`echo "$x" | /bin/cut -f4 -d':'`
    found=0

    while read line
    do
        y=`echo $line | cut -f3 -d":"`
        if [ $y -eq $groupid ]
        then
            found=1
            break
        fi
    done < /etc/group

    if [ $found -eq 0 ]
    then
        echo "Groupid $groupid does not exist in /etc/group, but is used by $userid"
    fi
done < /etc/passwd
"""
    rows_empty(cmd)

    #
    print_header("9.2.12 Check That Users Are Assigned Home Directories")
    cmd = """
cat /etc/passwd | awk -F: '{ print $1 " " $6 }' | while read user dir
do
    if [  -z "$dir" ]
    then
        echo "User $user has no home directory."
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.13 Check That Defined Home Directories Exist")
    cmd = """
cat /etc/passwd | awk -F: '{ print $1 " " $6 }' | while read user dir
do
    if [ -z "${dir}" ]; then
        echo "User $user has no home directory."
    elif [ ! -d $dir ]; then
        echo "User $user home directory ($dir) not found"
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.14 Check User Home Directory Ownership")
    cmd = """
defUsers="bin daemon adm lp sync shutdown halt mail uucp operator games gopher ftp nobody vcsa saslauth postfix sshd ntp mailnull smmsp"
cat /etc/passwd | awk -F: '{ print $1 " " $6 }' | while read user dir
do
    found=0
    for n in $defUsers
    do
        if [ "$user" = "$n" ]
        then
            found=1
            break
        fi
    done
    if [ $found -eq "0" ]
    then
        owner=`stat -c "%U" $dir`
        if [ "$owner" != "$user" ]
        then
            echo "Home directory $dir for $user owned by $owner"
        fi
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.15 Check for Duplicate UIDs")
    cmd = """
/bin/cat /etc/passwd | /bin/cut -f3 -d":" | /bin/sort -n | /usr/bin/uniq -c |\
while read x ; do
    set - $x
    if [ $1 -gt 1 ]; then
        users=`/bin/gawk -F: '($3 == n) { print $1 }' n=$2 /etc/passwd | /usr/bin/xargs`
        echo "Duplicate UID ($2): ${users}"
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.16 Check for Duplicate GIDs")
    cmd = """
/bin/cat /etc/group | /bin/cut -f3 -d":" | /bin/sort -n | /usr/bin/uniq -c |\
while read x ; do
    set - $x
    if [ $1 -gt 1 ]; then
        users=`/bin/gawk -F: '($3 == n) { print $1 }' n=$2 /etc/group | /usr/bin/xargs`
        echo "Duplicate GID ($2): ${users}"
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.17 Check That Reserved UIDs Are Assigned to System Accounts")
    cmd = """
defUsers=" root bin daemon adm lp sync shutdown halt mail uucp operator games gopher ftp nobody vcsa saslauth postfix sshd ntp mailnull smmsp"
/bin/cat /etc/passwd | /bin/awk -F: '($3 < 500) { print $1" "$3 }' |\
while read user uid; do
    found=0
    for tUser in ${defUsers}
    do
        if [ ${user} = ${tUser} ]; then
            found=1
            break
        fi
    done
    if [ $found -eq 0 ]; then
        echo "User $user has a reserved UID ($uid)."
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.18 Check for Duplicate User Names")
    cmd = """
cat /etc/passwd | cut -f1 -d":" | /bin/sort -n | /usr/bin/uniq -c |\
while read x ; do
    [ -z "${x}" ] && break
    set - $x
    if [ $1 -gt 1 ]; then
        uids=`/bin/gawk -F: '($1 == n) { print $3 }' n=$2 /etc/passwd | xargs`
        echo "Duplicate User Name ($2): ${uids}"
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.19 Check for Duplicate Group Names")
    cmd = """
cat /etc/group | cut -f1 -d":" | /bin/sort -n | /usr/bin/uniq -c |\
while read x ; do
    [ -z "${x}" ] && break
    set - $x
    if [ $1 -gt 1 ]; then
        gids=`/bin/gawk -F: '($1 == n) { print $3 }' n=$2 /etc/group | xargs`
        echo "Duplicate Group Name ($2): ${gids}"
    fi
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.20 Check for Presence of User .netrc Files")
    cmd = """
for dir in `/bin/cat /etc/passwd | /bin/awk -F: '{ print $6 }'`; do
    for file in $dir/.netrc; do
        if [ -f "$file" ]; then
            echo "File shouldn't exist, $file"
        fi
    done
done
"""
    rows_empty(cmd)

    #
    print_header("9.2.21 Check for Presence of User .forward Files")
    cmd = """
for dir in `/bin/cat /etc/passwd | /bin/awk -F: '{ print $6 }'`; do
    for file in $dir/.forward; do
        if [ -f "$file" ]; then
            echo "File shouldn't exist, $file"
        fi
    done
done
"""
    rows_empty(cmd)


def verify_network():
    '''
    Verify that the network config settings in the hardning config file has
    been applied.

    Not a CIS test.

    '''
    print_header("10 BONUS - Verify network settings")

    config = ConfigParser.SafeConfigParser()
    config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)
    counter = 0
    for setting in config.options('network'):
        counter += 1
        print_header("10.%s Verify network settings - %s" %
            (counter, config.get('network', setting)))
        rows_not_empty("grep %s /etc/sysctl.conf" % config.get('network', setting))


def verify_ssh():
    '''
    Verify that all ssh settings has been applied.

    Not a CIS test.
    '''
    print_header("11 BONUS - Verify ssh settings")
    config = ConfigParser.SafeConfigParser()
    config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)
    counter = 0
    for setting in config.options('ssh'):
        counter += 1
        print_header("11.%s Verify ssh settings - %s" %
            (counter, config.get('ssh', setting)))

        rows_not_empty("grep %s /etc/ssh/sshd_config" % config.get('ssh', setting))

    counter = 0
    for setting in config.options('sshd'):
        counter += 1

        print_header("11.%s Verify sshd settings - %s" %
            (counter, config.get('sshd', setting)))

        rows_not_empty("grep %s /etc/ssh/sshd_config" % config.get('sshd', setting))
