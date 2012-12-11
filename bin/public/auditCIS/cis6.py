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
print_header("6 System Access, Authentication and Authorization")

#
print_header("6.1 Configure cron and anacron")

#
print_header("6.1.1 Enable anacron Daemon (Scored)")
check_equal("rpm -q anacron", "package anacron is not installed")
print_info("Not installed syco servers.")

print_header("6.1.2 Enable crond Daemon (Scored)")
check_equal_re(
    "chkconfig --list crond",
    "crond.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
)

#
print_header("6.1.3 Set User/Group Owner and Permission on /etc/anacrontab (Scored)")
check_equal('stat -c "%a %u %g" /etc/anacrontab | egrep "600 0 0"', "600 0 0")

#
print_header("6.1.4 Set User/Group Owner and Permission on /etc/crontab (Scored)")
check_equal('stat -c "%a %u %g" /etc/crontab | egrep "600 0 0"', "600 0 0")

#
print_header("6.1.5 Set User/Group Owner and Permission on /etc/cron.hourly (Scored)")
check_equal('stat -c "%a %u %g" /etc/cron.hourly | egrep "600 0 0"', "600 0 0")

#
print_header("6.1.6 Set User/Group Owner and Permission on /etc/cron.daily (Scored)")
check_equal('stat -c "%a %u %g" /etc/cron.daily | egrep "600 0 0"', "600 0 0")

#
print_header("6.1.7 Set User/Group Owner and Permission on /etc/cron.weekly (Scored)")
check_equal('stat -c "%a %u %g" /etc/cron.weekly | egrep "600 0 0"', "600 0 0")

#
print_header("6.1.8 Set User/Group Owner and Permission on /etc/cron.monthly (Scored)")
check_equal('stat -c "%a %u %g" /etc/cron.monthly | egrep "600 0 0"', "600 0 0")

#
print_header("6.1.9 Set User/Group Owner and Permission on /etc/cron.d (Scored)")
check_equal('stat -c "%a %u %g" /etc/cron.d | egrep "700 0 0"', "700 0 0")
check_empty('stat -c "%a %u %g" /etc/cron.d/* | egrep -v "600 0 0"')

#
print_header("6.1.10 Restrict at Daemon (Scored)")
check_equal('ls /etc/at.deny', "ls: cannot access /etc/at.deny: No such file or directory")
check_equal('stat -c "%a %u %g" /etc/at.allow | egrep "600 0 0"', "600 0 0")

#
print_header("6.1.11 Restrict at/cron to Authorized Users (Scored)")
check_equal('ls /etc/cron.deny', "ls: cannot access /etc/cron.deny: No such file or directory")
check_equal('stat -c "%a %u %g" /etc/cron.allow | egrep "600 0 0"', "600 0 0")

#
print_header("6.2 Configure SSH")

#
print_header("6.2.1 Set SSH Protocol to 2 (Scored)")
check_equal(
    'grep "^Protocol" /etc/ssh/sshd_config',
    "Protocol 2"
)

#
print_header("6.2.2 Set LogLevel to INFO (Scored)")
check_equal(
    'grep "^LogLevel" /etc/ssh/sshd_config',
    "LogLevel INFO"
)

#
print_header("6.2.3 Set Permissions on /etc/ssh/sshd_config (Scored)")
check_equal('stat -c "%a %u %g" /etc/ssh/sshd_config | egrep "600 0 0"', "600 0 0")

#
print_header("6.2.4 Disable SSH X11 Forwarding (Scored)")
check_equal(
    'grep "^X11Forwarding" /etc/ssh/sshd_config',
    "X11Forwarding no"
)

#
print_header("6.2.5 Set SSH MaxAuthTries to 4 or Less (Scored)")
check_equal(
    'grep "^MaxAuthTries" /etc/ssh/sshd_config',
    "MaxAuthTries 4"
)

#
print_header("6.2.6 Set SSH IgnoreRhosts to Yes (Scored)")
check_equal(
    'grep "^IgnoreRhosts" /etc/ssh/sshd_config',
    "IgnoreRhosts yes"
)

#
print_header("6.2.7 Set SSH HostbasedAuthentication to No (Scored)")
check_equal(
    'grep "^HostbasedAuthentication" /etc/ssh/sshd_config',
    "HostbasedAuthentication no"
)

#
print_header("6.2.8 Disable SSH Root Login (Scored)")
check_equal(
    'grep "^PermitRootLogin" /etc/ssh/sshd_config',
    "PermitRootLogin no"
)

#
print_header("6.2.9 Set SSH PermitEmptyPasswords to No (Scored)")
check_equal(
    'grep "^PermitEmptyPasswords" /etc/ssh/sshd_config',
    "PermitEmptyPasswords no"
)

#
print_header("6.2.10 Do Not Allow Users to Set Environment Options (Scored)")
check_equal(
    'grep PermitUserEnvironment /etc/ssh/sshd_config',
    "PermitUserEnvironment no"
)

#
print_header("6.2.11 Use Only Approved Cipher in Counter Mode (Scored)")
# CIS accepts Ciphers aes128-ctr,aes192-ctr,aes256-ctr
check_equal(
    'grep "Cipher" /etc/ssh/sshd_config',
    "Ciphers aes256-ctr"
)

#
print_header("6.2.12 Set Idle Timeout Interval for User Login (Scored)")
check_equal(
    'grep "^ClientAliveInterval" /etc/ssh/sshd_config',
    "ClientAliveInterval 900"
)
check_equal(
    'grep "^ClientAliveCountMax" /etc/ssh/sshd_config',
    "ClientAliveCountMax 0"
)

#
print_header("6.2.13 Limit Access via SSH (Scored)")
print_info(
    "User restrictions are not set in sshd_config, we restrict with LDAP."
)

#
print_header("6.2.14 Set SSH Banner (Scored)")
check_equal(
    "grep '^Banner' /etc/ssh/sshd_config",
    "Banner /etc/issue.net"
)

#
print_header("6.3 Configure PAM")

#
print_header("6.3.1 Upgrade Password Hashing Algorithm to SHA-512 (Scored)")
check_equal(
    "authconfig --test | grep hashing | grep sha512",
    "password hashing algorithm is sha512"
)


#
print_header("6.3.2 Set Password Creation Requirement Parameters Using pam_cracklib (Scored)")
check_equal(
    "grep pam_cracklib.so /etc/pam.d/system-auth",
    "password    requisite     pam_cracklib.so try_first_pass " +
    "retry=3 minlen=14,dcredit=-1,ucredit=-1,ocredit=-2,lcredit=-1,difok=3"
)

#
print_header("6.3.3 Set Strong Password Creation Policy Using pam_passwdqc (Scored)")
print_info("We are using pam_cracklib")

#
print_header("6.3.4 Set Lockout for Failed Password Attempts (Not Scored)")
print_info("  TODO: Implement this.")

#
print_header("6.3.5 Use pam_deny.so to Deny Services (Not Scored)")
print_header("  TODO: Implement this.")

#
print_header("6.3.6 Limit Password Reuse (Scored)")
check_equal(
    "grep 'remember' /etc/pam.d/system-auth",
    "password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok remember=5"
)

#
print_header("6.4 Restrict root Login to System Console (Not Scored)")
check_equal("cat /etc/securetty", "tty1")

#
print_header("6.5 Restrict Access to the su Command (Scored)")
check_equals(
    'grep pam_wheel.so /etc/pam.d/su',
    (
        "#auth\t\tsufficient\tpam_wheel.so trust use_uid",
        "auth\t\trequired\tpam_wheel.so use_uid"
    )
)
check_equal(
    "grep wheel /etc/group",
    "wheel:x:10:"
)
