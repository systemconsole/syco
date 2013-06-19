#!/usr/bin/env python
'''
Remove packages listed in hardening/config.cfg - part of the hardening.

'''
from general import get_install_dir

__author__ = "daniel@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from general import x
from scopen import scOpen
import app
import config


def setup_common():
    yum_update()
    customize_shell()
    create_syco_modprobe()
    time_out()
    disable_usb()
    forward_root_mail()
    general_cis()


def yum_update():
  '''
  yum update is the first thing that is done when hardening the server,
  to minimize the risk that an updated package revert any hardening mods.
  '''
  app.print_verbose("Update with yum")
  x("yum update -y")


def customize_shell():
    app.print_verbose("Customize shell")

    app.print_verbose("  Add Date And Time To History Output")
    scOpen("/etc/bashrc").replace_add(
        "^export HISTTIMEFORMAT=.*$",
        "export HISTTIMEFORMAT=\"%h/%d - %H:%M:%S \""
    )

    app.print_verbose("  Add Color To Grep")
    root = scOpen("/root/.bash_profile")
    root.replace_add("^export GREP_COLOR=.*$",   "export GREP_COLOR='1;32'")
    root.replace_add("^export GREP_OPTIONS=.*$", "export GREP_OPTIONS=--color=auto")

    skel = scOpen("/etc/skel/.bash_profile")
    skel.replace_add("^export GREP_COLOR=.*$",   "export GREP_COLOR='1;32'")
    skel.replace_add("^export GREP_OPTIONS=.*$", "export GREP_OPTIONS=--color=auto")

    app.print_verbose("  Enable SSH key forwarding to work with sudo su")
    tmp_sudo_file = get_install_dir() + "sudoers"
    x("cp /etc/sudoers " + tmp_sudo_file)
    sudoers = scOpen(tmp_sudo_file)
    sudoers.remove("Defaults    env_keep += \"SSH_AUTH_SOCK\"")
    sudoers.add("Defaults    env_keep += \"SSH_AUTH_SOCK\"")
    xRes = x("visudo -c -f " + tmp_sudo_file)
    if tmp_sudo_file + ": parsed OK" in xRes:
        x("mv " + tmp_sudo_file + " /etc/sudoers")
    else:
        app.print_error("Temporary sudoers file corrupt, not updating")

def create_syco_modprobe():
    x("touch /etc/modprobe.d/syco.conf")
    x("chown root:root /etc/modprobe.d/syco.conf")
    x("chmod 644 /etc/modprobe.d/syco.conf")
    x("chcon system_u:object_r:modules_conf_t:s0 /etc/modprobe.d/syco.conf")


def time_out():
    #Timing out users from there shell after 15 min
    profile = scOpen("/etc/profile")
    profile.replace_add("^export TMOUT=.*$",   "export TMOUT=900")


def disable_usb():
    # TODO Currently need usb dvd reader for installation and keyboard.
    return
    app.print_verbose("Disable usb")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^blacklist usb-storage$", "blacklist usb-storage"
    )


def forward_root_mail():
    app.print_verbose("Forward all root email to " + config.general.get_admin_email())
    scOpen("/etc/aliases").replace_add(
        ".*root[:].*", "root:     " + config.general.get_admin_email()
    )
    x("/usr/bin/newaliases")


def general_cis():
    '''General CIS hardenings'''
    #
    app.print_verbose("CIS 1.1.2 Set nodev option for /tmp Partition")
    app.print_verbose("CIS 1.1.3 Set nosuid option for /tmp Partition")
    app.print_verbose("CIS 1.1.4 Set noexec option for /tmp Partition")
    scOpen("/etc/fstab").replace_ex(
        "/tmp ", "noexec[^0-9]*", "noexec,nodev,nosuid "
    )
    x("mount -o remount,noexec,nodev,nosuid /tmp")

    app.print_verbose("1.1.6 Bind Mount the /var/tmp directory to /tmp")
    scOpen("/etc/fstab").replace_ex(
        "/var/tmp ", "noexec[^0-9]*", "noexec,nodev,nosuid "
    )
    x("mount -o remount,noexec,nodev,nosuid /var/tmp")

    #
    app.print_verbose("CIS 1.1.10 Add nodev Option to /home")
    scOpen("/etc/fstab").replace_ex(
        "/home", "noexec[^0-9]*", "noexec,nodev,nosuid "
    )
    x("mount -o remount,noexec,nodev /home")

    #
    app.print_verbose("CIS 1.1.14 Add nodev Option to /dev/shm Partition")
    app.print_verbose("CIS 1.1.15 Add nosuid Option to /dev/shm Partition")
    app.print_verbose("CIS 1.1.16 Add noexec Option to /dev/shm Partition")
    scOpen("/etc/fstab").replace_ex(
        "/dev/shm", "defaults[^0-9]*", "defaults,nodev,nosuid,noexec "
    )
    x("mount -o remount,nodev,nosuid,noexec /dev/shm")

    app.print_verbose("CIS 1.1.17 Set Sticky Bit on All World-Writable Directories")
    x("find / -type d -perm -0002 -exec chmod a+t {} \; 2>/dev/null")

    #
    app.print_verbose("CIS 1.1.18 Disable Mounting of cramfs Filesystems")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install cramfs /bin/true$", "install cramfs /bin/true"
    )

    #
    app.print_verbose("CIS 1.1.19 Disable Mounting of freevxfs Filesystems")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install freevxfs /bin/true$", "install freevxfs /bin/true"
    )

    #
    app.print_verbose("CIS 1.1.20 Disable Mounting of jffs2 Filesystems")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install jffs2 /bin/true$", "install jffs2 /bin/true"
    )

    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install zlib_deflate /bin/true$", "install zlib_deflate /bin/true"
    )

    #
    app.print_verbose("CIS 1.1.21 Disable Mounting of hfs Filesystems")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install hfs /bin/true$", "install hfs /bin/true"
    )

    #
    app.print_verbose("CIS 1.1.22 Disable Mounting of hfsplus Filesystems")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install hfsplus /bin/true$", "install hfsplus /bin/true"
    )

    #
    app.print_verbose("CIS 1.1.23 Disable Mounting of squashfs Filesystems")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install squashfs /bin/true$", "install squashfs /bin/true"
    )

    #
    app.print_verbose("CIS 1.1.24 Disable Mounting of udf Filesystems")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install udf /bin/true$", "install udf /bin/true"
    )

    #
    app.print_verbose("CIS 1.5.1 Set User/Group Owner on /etc/grub.conf (Scored)")
    x("chown root:root /etc/grub.conf")

    #
    app.print_verbose("CIS 1.5.2 Set Permissions on /etc/grub.conf (Scored)")
    x("chmod og-rwx /etc/grub.conf")

    #
    app.print_verbose("CIS 1.5.4 Require Authentication for Single-User Mode (Scored)")
    x('sed -i "/SINGLE/s/sushell/sulogin/" /etc/sysconfig/init')
    x('sed -i "/PROMPT/s/yes/no/" /etc/sysconfig/init')

    #
    app.print_verbose("CIS 1.6.1 Restrict Core Dumps")
    scOpen("/etc/security/limits.conf").replace_add(
        "^\* hard core 0", "* hard core 0"
    )

    #
    app.print_verbose("CIS 3.1 Set Daemon umask")
    scOpen("/etc/sysconfig/init").replace_add(
        "^umask.*", "umask 027"
    )

    #
    app.print_verbose("CIS 4.5 Install TCP Wrappers")
    x("""[ "`rpm -q tcp_wrappers`" == 'package tcp_wrappers is not installed' ]\
         && yum install -y tcp_wrappers""")

    #
    app.print_verbose("CIS 4.8.1 Disable DCCP")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install dccp /bin/true$", "install dccp /bin/true"
    )

    #
    app.print_verbose("CIS 4.8.2 Disable SCTP")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install sctp /bin/true$", "install sctp /bin/true"
    )

    #
    app.print_verbose("CIS 4.8.3 Disable RDS")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install rds /bin/true$", "install rds /bin/true"
    )

    #
    app.print_verbose("CIS 4.8.4 Disable TIPC")
    scOpen("/etc/modprobe.d/syco.conf").replace_add(
        "^install tipc /bin/true$", "install tipc /bin/true"
    )

    #
    app.print_verbose("CIS 6.1.4 Set User/Group Owner and Permission on /etc/crontab")
    x("chown root:root /etc/crontab")
    x("chmod og-rwx /etc/crontab")

    #
    app.print_verbose("CIS 6.1.5 Set User/Group Owner and Permission on /etc/cron.hourly")
    x("chown root:root /etc/crontab")
    x("chmod og-rwx /etc/crontab")

    #
    app.print_verbose("CIS 6.1.6 Set User/Group Owner and Permission on /etc/cron.daily")
    x("chown root:root /etc/cron.daily")
    x("chmod og-rwx /etc/cron.daily")

    #
    app.print_verbose("CIS 6.1.7 Set User/Group Owner and Permission on /etc/cron.weekly")
    x("chown root:root /etc/cron.weekly")
    x("chmod og-rwx /etc/cron.weekly")

    #
    app.print_verbose("CIS 6.1.8 Set User/Group Owner and Permission on /etc/cron.monthly")
    x("chown root:root /etc/cron.monthly")
    x("chmod og-rwx /etc/cron.monthly")

    #
    app.print_verbose("CIS 6.1.9 Set User/Group Owner and Permission on /etc/cron.d")
    x("chown -R root:root /etc/cron.d")
    x("chmod 700 /etc/cron.d")
    x("chmod 600 /etc/cron.d/*")

    #
    app.print_verbose("CIS 6.1.10 Restrict at Daemon (Scored)")
    x("rm -f /etc/at.deny")
    x("touch /etc/at.allow")
    x("chown root:root /etc/at.allow")
    x("chmod 600 /etc/at.allow")

    #
    app.print_verbose("CIS 6.1.11 Restrict at/cron to Authorized Users (Scored)")
    x("/bin/rm -f /etc/cron.deny")
    x("touch /etc/cron.allow")
    x("chmod 600 /etc/cron.allow")
    x("chown root:root /etc/cron.allow")

    #
    app.print_verbose("CIS 9.2.13 Check That Defined Home Directories Exist")
    x("mkdir -p /var/adm")
    x("mkdir -p /var/spool/uucp")
    x("mkdir -p /var/gopher")
    x("mkdir -p /var/ftp")
    x("mkdir -p /var/empty/saslauth")


    #
    # Aftermatch
    #
    x("sysctl -e -p")
