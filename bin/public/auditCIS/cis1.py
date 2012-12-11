#!/usr/bin/env python
'''
A module to the CIS audit.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from utils import check_empty, check_equal, check_equal_re, check_equals, check_not_empty, check_return_code, print_header, view_output, print_warning, print_info

#
print_header("1. Install Updates, Patches and Additional Security Software")

#
print_header("1.1 Filesystem Configuration")

#
print_header("1.1.1 Create Separate Partition for /tmp (Scored)")
check_equal('grep "[[:space:]]/tmp[[:space:]]" /etc/fstab', '/tmp')

#
print_header("1.1.2 Set nodev option for /tmp Partition (Scored)")
# No tmp partition should have nodev.
check_equal("grep /tmp /etc/fstab", "nodev")
check_equal("mount | grep /tmp", "nodev")

#
print_header("1.1.3 Set nosuid option for /tmp Partition (Scored)")
# No tmp partition should have nosuid.
check_equal("grep /tmp /etc/fstab", "nosuid")
check_equal("mount | grep /tmp", "nosuid")

#
print_header("1.1.4 Set noexec option for /tmp Partition (Scored)")
# No tmp partition should have noexec.
check_equal("grep /tmp /etc/fstab", "noexec")
check_equal("mount | grep /tmp", "noexec")

#
print_header("1.1.5 Create Separate Partition for /var (Scored)")
check_equal("grep '/var ' /etc/fstab", "var")

#
print_header("1.1.6 Bind Mount the /var/tmp directory to /tmp")
check_equal("grep '/var/tmp ' /etc/fstab", "/var/tmp")
check_equal("mount | grep '/var/tmp ' | grep nodev", "nodev")
check_equal("mount | grep '/var/tmp ' | grep nosuid", "nosuid")
check_equal("mount | grep '/var/tmp ' | grep noexec", "noexec")
print_info("Not applicable, syco uses a separate partion for /var/tmp")

#
print_header("1.1.7 Create Separate Partition for /var/log (Scored)")
check_equal("grep '/var/log ' /etc/fstab", "/var/log")

#
print_header("1.1.8 Create Separate Partition for /var/log/audit (Scored)")
check_equal("grep '/var/log/audit ' /etc/fstab", "/var/log/audit")

#
print_header("1.1.9 Create Separate Partition for /home (Scored)")
check_equal("grep '/home ' /etc/fstab", "/home")

#
print_header("1.1.10 Add nodev Option to /home (Scored)")
check_equal("grep /home /etc/fstab", "nodev")
check_equal("mount | grep /home", "nodev")

#
print_header("1.1.11 Add nodev Option to Removable Media Partitions (Not Scored)")
print_warning("Check manually for nodev on removable media.")
view_output("cat /etc/fstab")

#
print_header("1.1.12 Add noexec Option to Removable Media Partitions (Not Scored)")
print_warning("Check manually for noexec on removable media.")
view_output("cat /etc/fstab")

#
print_header("1.1.13 Add nosuid Option to Removable Media Partitions (Not Scored)")
print_warning("Check manually for nosuid on removable media.")
view_output("cat /etc/fstab")

#
print_header("1.1.14 Add nodev Option to /dev/shm Partition (Scored)")
check_equal("grep /dev/shm /etc/fstab | grep nodev", "nodev")
check_equal("mount | grep /dev/shm | grep nodev", "nodev")

#
print_header("1.1.15 Add nosuid Option to /dev/shm Partition (Scored)")
check_equal("grep /dev/shm /etc/fstab | grep nosuid", "nosuid")
check_equal("mount | grep /dev/shm | grep nosuid", "nosuid")

#
print_header("1.1.16 Add noexec Option to /dev/shm Partition (Scored)")
check_equal("grep /dev/shm /etc/fstab | grep noexec", "noexec")
check_equal("mount | grep /dev/shm | grep noexec", "noexec")

#
print_header("1.1.17 Set Sticky Bit on All World-Writable Directories (Scored)")
check_empty("find / -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null")

#
print_header("1.1.18 Disable Mounting of cramfs Filesystems (Not Scored)")
check_equal("/sbin/modprobe -n -v cramfs", "install /bin/true")
check_empty("/sbin/lsmod | grep cramfs")

#
print_header("1.1.19 Disable Mounting of freevxfs Filesystems (Not Scored)")
check_equal("/sbin/modprobe -n -v freevxfs", "install /bin/true")
check_empty("/sbin/lsmod | grep freexvfs")

#
print_header("1.1.20 Disable Mounting of jffs2 Filesystems (Not Scored)")
check_equal("/sbin/modprobe -n -v jffs2", "install /bin/true")
check_empty("/sbin/lsmod | grep jffs2")

#
print_header("1.1.21 Disable Mounting of hfs Filesystems (Not Scored)")
check_equal("/sbin/modprobe -n -v hfs", "install /bin/true")
check_empty("/sbin/lsmod | grep hfs")

#
print_header("1.1.22 Disable Mounting of hfsplus Filesystems (Not Scored)")
check_equal("/sbin/modprobe -n -v hfsplus", "install /bin/true")
check_empty("/sbin/lsmod | grep hfsplus")

#
print_header("1.1.23 Disable Mounting of squashfs Filesystems (Not Scored)")
check_equal("/sbin/modprobe -n -v squashfs", "install /bin/true")
check_empty("/sbin/lsmod | grep squashfs")

#
print_header("1.1.24 Disable Mounting of udf Filesystems (Not Scored)")
check_equals(
    '/sbin/modprobe -n -v udf',
    (None, "install /bin/true")
)
check_empty("/sbin/lsmod | grep udf")

#
print_header("1.2 Configure Software Updates")

#
print_header("1.2.1 Configure Connection to the RHN RPM Repositories (Not Scored)")
check_return_code("yum check-update", 0)
print_info(
    "We are using centos and not red hat. Check manually if we are " +
    "connected to sunet."
)

#
print_header("1.2.2 Verify Red Hat GPG Key is Installed (Scored)")
check_equal(
    'rpm -q --queryformat "%{SUMMARY}\\n" gpg-pubkey',
    'gpg(CentOS-6 Key (CentOS 6 Official Signing Key) <centos-6-key@centos.org>)'
)
check_equals(
    'gpg --quiet --with-fingerprint /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-6',
    (
        "pub  4096R/C105B9DE 2011-07-03 CentOS-6 Key (CentOS 6 Official Signing Key) <centos-6-key@centos.org>",
        "      Key fingerprint = C1DA C52D 1664 E8A4 386D  BA43 0946 FCA2 C105 B9DE"
    )
)

#
print_header("1.2.3 Verify that gpgcheck is Globally Activated (Scored)")
check_equal("grep gpgcheck /etc/yum.conf", "gpgcheck=1")

#
print_header("1.2.4 Disable the rhnsd Daemon (Not Scored)")
check_empty("chkconfig --list | grep rhnsd")

#
print_header("1.2.5 Obtain Software Package Updates with yum (Not Scored)")
check_return_code("yum check-update", 0)

#
print_header("1.2.6 Verify Package Integrity Using RPM (Not Scored)")
print_warning("Check manually if any packages has been changed.")
view_output("rpm -qVa | awk '$2 != \"c\" { print $0}'")

#
print_header("1.3 Advanced Intrusion Detection Environment (AIDE)")
print_info("We are using ossec instead of AIDE.")

#
print_header("1.4 Configure SELinux")

#
print_header("1.4.1 Enable SELinux in /etc/grub.conf (Scored)")
check_empty("grep selinux=0 /etc/grub.conf")
check_empty("grep enforcing=0 /etc/grub.conf")

#
print_header("1.4.2 Set the SELinux State (Scored)")
check_equal('grep SELINUX=enforcing /etc/selinux/config', "SELINUX=enforcing")

check_equals(
    '/usr/sbin/sestatus',
    (
        "SELinux status:                 enabled",
        "SELinuxfs mount:                /selinux",
        "Current mode:                   enforcing",
        "Mode from config file:          enforcing",
        "Policy version:                 24",
        "Policy from config file:        targeted"
    )
)
#
print_header("1.4.3 Set the SELinux Policy (Scored)")
check_equal(
    'grep SELINUXTYPE=targeted /etc/selinux/config',
    "SELINUXTYPE=targeted"
)

check_equals(
    '/usr/sbin/sestatus',
    (
        "SELinux status:                 enabled",
        "SELinuxfs mount:                /selinux",
        "Current mode:                   enforcing",
        "Mode from config file:          enforcing",
        "Policy version:                 24",
        "Policy from config file:        targeted"
    )
)

#
print_header("1.4.4 Remove SETroubleshoot (Scored)")
check_empty("chkconfig --list | grep setroubleshoot")

#
print_header("1.4.5 Remove MCS Translation Service (mcstrans) (Scored)")
check_empty("chkconfig --list | grep mctrans")

#
print_header("1.4.6 Check for Unconfined Daemons (Scored)")
check_empty('ps -eZ | egrep "initrc" | egrep -vw "tr|ps|egrep|bash|awk" | tr ":" " " | awk "{print $NF }"')

#
print_header("1.5 Secure Boot Settings")

#
print_header("1.5.1 Set User/Group Owner on /etc/grub.conf (Scored)")
check_equal(
    'stat -c "%u %g" /etc/grub.conf | egrep "0 0"',
    "0 0"
)

#
print_header("1.5.2 Set Permissions on /etc/grub.conf (Scored)")
check_equal(
    'stat -L -c "%a" /etc/grub.conf | egrep ".00"',
    "600"
)

#
print_header("1.5.3 Set Boot Loader Password (Scored)")
check_equal('grep "^password" /etc/grub.conf', "password --encrypted")

#
print_header("1.5.4 Require Authentication for Single-User Mode (Scored)")
check_equal('grep SINGLE /etc/sysconfig/init', "SINGLE=/sbin/sulogin")
check_equal('grep "PROMPT" /etc/sysconfig/init', "PROMPT=no")

#
print_header("1.5.5 Disable Interactive Boot (Scored)")
check_equal('grep "^PROMPT=" /etc/sysconfig/init', 'PROMPT=no')

#
print_header("1.6 Additional Process Hardening")

#
print_header("1.6.1 Restrict Core Dumps (Scored)")
check_equal(
    'grep "hard core" /etc/security/limits.conf',
    "* hard core 0"
)

check_equal(
    'sysctl fs.suid_dumpable',
    "fs.suid_dumpable = 0"
)

#
print_header("1.6.2 Configure ExecShield (Scored)")
check_equal(
    "sysctl kernel.exec-shield",
    "kernel.exec-shield = 1"
)

#
print_header("1.6.3 Enable Randomized Virtual Memory Region Placement (Scored)")
check_equal(
    "sysctl kernel.randomize_va_space",
    "kernel.randomize_va_space = 2"
)

#
print_header("1.7 Use the Latest OS Release (Not Scored)")
print_warning("Check manually for latest os release")
view_output("uname -ra")
view_output("cat /etc/redhat-release")
