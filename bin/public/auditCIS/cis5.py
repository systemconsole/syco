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

import config

#
print_header("5 Logging and Auditing")

#
print_header("5.1 Configure Syslog")

#
print_header("5.1.1 Install the rsyslog package (Scored)")
check_equal_re(
    "rpm -q rsyslog",
    "rsyslog.*"
)

#
print_header("5.1.2 Activate the rsyslog Service (Scored)")
check_equal(
    "rpm -q syslog",
    "package syslog is not installed"
)
check_empty("chkconfig --list | grep syslog")
check_equal_re(
    "chkconfig --list rsyslog",
    "rsyslog.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
)

#
print_header("5.1.3 Configure /etc/rsyslog.conf (Not Scored)")
print_warning("Manually review the contents of the /etc/rsyslog.conf file to ensure appropriate logging is set. ")
view_output("ls -l /var/log/")

#
print_header("5.1.4 Create and Set Permissions on rsyslog Log Files (Scored)")
print_header(" TODO - Ensure that the log files are logging information")

#
print_header("5.1.5 Configure rsyslog to Send Logs to a Remote Log Host (Scored)")
expect = "^*.*[^I][^I]*@{0}".format(config.general.get_log_server_hostname1())
check_equal(
    "grep '%s' /etc/rsyslog.conf" % expect,
    expect
)

expect = "^*.*[^I][^I]*@{0}".format(config.general.get_log_server_hostname2())
check_equal(
    "grep '%s' /etc/rsyslog.conf" % expect,
    expect
)
#
check_empty('rpm -q rsyslog|grep  "package rsyslog is not installed"')


#
print_header("5.1.6 Accept Remote rsyslog Messages Only on Designated Log Hosts (Not Scored)")
check_equal(
    "grep '^\$ModLoad.*imtcp' /etc/rsyslog.conf",
    "$ModLoad imudp"
)
check_equal(
    "grep '^\$InputTCPServerRun' /etc/rsyslog.conf",
    "$InputTCPServerRun 514"
)

#
print_header("5.1.7 - BONUS ")
check_equal(
    "grep '^authpriv\\.\\*' /etc/rsyslog.conf",
    "authpriv.*"
)

#
print_header("5.2 Configure System Accounting (auditd)")

#
print_header("5.2.1 Configure Data Retention")

#
print_header("5.2.1.1 Configure Audit Log Storage Size (Not Scored)")
check_equal(
    "grep 'max_log_file[[:space:]]*\=' /etc/audit/auditd.conf",
    "max_log_file = 50"
)

#
print_header("5.2.1.2 Disable System on Audit Log Full (Not Scored)")
check_equal(
    "grep '^space_left_action[[:space:]]*\=' /etc/audit/auditd.conf",
    "space_left_action = email"
)

check_equal(
    "grep action_mail_acct /etc/audit/auditd.conf",
    "action_mail_acct = root"
)

check_equal(
    "grep admin_space_left_action /etc/audit/auditd.conf",
    "admin_space_left_action = halt"
)

#
print_header("5.2.1.3 Keep All Auditing Information (Scored)")
check_equal(
    "grep max_log_file_action /etc/audit/auditd.conf",
    "max_log_file_action = keep_logs"
)

#
print_header("5.2.2 Enable auditd Service (Scored)")
check_equal_re(
    "rpm -q audit",
    "audit.*"
)
check_equal_re(
    "chkconfig --list auditd",
    "auditd.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
)

#
print_header("5.2.3 Enable Auditing for Processes That Start Prior to auditd (Scored)")
check_equal(
    'grep "^[^#]*kernel" /etc/grub.conf|grep "audit=1"',
    'audit=1'
)

#
print_header("5.2.4 Record Events That Modify Date and Time Information (Scored)")
check_equals(
    'grep time-change /etc/audit/audit.rules',
    (
        "-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change",
        "-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change",
        "-a always,exit -F arch=b64 -S clock_settime -k time-change",
        "-a always,exit -F arch=b32 -S clock_settime -k time-change",
        "-w /etc/localtime -p wa -k time-change"
    )
)

#
print_header("5.2.5 Record Events That Modify User/Group Information (Scored)")
check_equals(
    'grep identity /etc/audit/audit.rules',
    (
        "-w /etc/group -p wa -k identity",
        "-w /etc/passwd -p wa -k identity",
        "-w /etc/gshadow -p wa -k identity",
        "-w /etc/shadow -p wa -k identity",
        "-w /etc/security/opasswd -p wa -k identity"
    )
)

#
print_header("5.2.6 Record Events That Modify the System's Network Environment (Scored)")
check_equals(
    'grep system-locale /etc/audit/audit.rules',
    (
        "-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale",
        "-a always,exit -F arch=b32 -S sethostname -S setdomainname -k system-locale",
        "-w /etc/issue -p wa -k system-locale",
        "-w /etc/issue.net -p wa -k system-locale",
        "-w /etc/hosts -p wa -k system-locale",
        "-w /etc/sysconfig/network -p wa -k system-locale"
    )
)

#
print_header("5.2.7 Record Events That Modify the System's Mandatory Access Controls (Scored)")
check_equal(
    "grep MAC-policy /etc/audit/audit.rules",
    "-w /etc/selinux/ -p wa -k MAC-policy"
)

#
print_header("5.2.8 Collect Login and Logout Events (Scored)")
check_equals(
    'grep logins /etc/audit/audit.rules',
    (
        "-w /var/log/faillog -p wa -k logins",
        "-w /var/log/lastlog -p wa -k logins",
        "## TODO Don't work?? -w /var/log/tallylog -p -wa -k logins"
    )
)

#
print_header("5.2.9 Collect Session Initiation Information (Scored)")
check_equals(
    'grep session /etc/audit/audit.rules',
    (
        "-w /var/log/btmp -p wa -k session",
        "-w /var/run/utmp -p wa -k session",
        "-w /var/log/wtmp -p wa -k session"
    )
)

#
print_header("5.2.10 Collect Discretionary Access Control Permission Modification Events (Scored)")
check_equals(
    'grep perm_mod /etc/audit/audit.rules',
    (
        "-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=500 -F auid!=4294967295 -k perm_mod",
        "-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -F auid>=500 -F auid!=4294967295 -k perm_mod",
        "-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -F auid>=500 -F auid!=4294967295 -k perm_mod",
        "-a always,exit -F arch=b32 -S chown -S fchown -S fchownat -S lchown -F auid>=500 -F auid!=4294967295 -k perm_mod",
        "-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=500 -F auid!=4294967295 -k perm_mod",
        "-a always,exit -F arch=b32 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=500 -F auid!=4294967295 -k perm_mod"
    )
)

#
print_header("5.2.11 Collect Unsuccessful Unauthorized Access Attempts to Files (Scored)")
check_equals(
    'grep access /etc/audit/audit.rules',
    (
        "-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=500 -F auid!=4294967295 -k access",
        "-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=500 -F auid!=4294967295 -k access",
        "-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=500 -F auid!=4294967295 -k access",
        "-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=500 -F auid!=4294967295 -k access"
    )
)

#
print_header("5.2.12 Collect Use of Privileged Commands (Scored)")
print_header(" TODO: need remediation")
#find / -xdev \( -perm -4000 -o -perm -2000 \) -type f | awk '{print "-a always,exit -F path=" $1 " -F perm=x -F auid>=500 -F auid!=4294967295 -k privileged" }'
check_equal(
    "",
    ""
)

#
print_header("5.2.13 Collect Successful File System Mounts (Scored)")
check_equals(
    'grep mounts /etc/audit/audit.rules',
    (
        "-a always,exit -F arch=b64 -S mount -F auid>=500 -F auid!=4294967295 -k mounts",
        "-a always,exit -F arch=b32 -S mount -F auid>=500 -F auid!=4294967295 -k mounts"
    )
)

#
print_header("5.2.14 Collect File Deletion Events by User (Scored)")
check_equals(
    'grep delete$ /etc/audit/audit.rules',
    (
        "-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=500 -F auid!=4294967295 -k delete",
        "-a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=500 -F auid!=4294967295 -k delete"
    )
)

#
print_header("5.2.15 Collect Changes to System Administration Scope (sudoers) (Scored)")
check_equal(
    "grep scope$ /etc/audit/audit.rules",
    "-w /etc/sudoers -p wa -k scope"
)

#
print_header("5.2.16 Collect System Administrator Actions (sudolog) (Scored)")
check_equal(
    "grep actions /etc/audit/audit.rules",
    "-w /var/log/sudo.log -p wa -k actions"
)

#
print_header("5.2.17 Collect Kernel Module Loading and Unloading (Scored)")
check_equals(
    'grep modules /etc/audit/audit.rules',
    (
        "-w /sbin/insmod -p x -k modules",
        "-w /sbin/rmmod -p x -k modules",
        "-w /sbin/modprobe -p x -k modules",
        "-a always,exit -F arch=b64 -S init_module -S delete_module -k modules"
    )
)

#
print_header("5.2.18 Make the Audit Configuration Immutable (Scored)")
check_equal(
    'grep "^-e 2" /etc/audit/audit.rules',
    "-e 2"
)

#
print_header("5.3 Configure logrotate (Not Scored)")
check_equal("grep '/var/log/cron' /etc/logrotate.d/syslog", "/var/log/cron")
check_equal("grep '/var/log/maillog' /etc/logrotate.d/syslog", "/var/log/maillog")
check_equal("grep '/var/log/messages' /etc/logrotate.d/syslog", "/var/log/messages")
check_equal("grep '/var/log/secure' /etc/logrotate.d/syslog", "/var/log/secure")
check_equal("grep '/var/log/spoole' /etc/logrotate.d/syslog", "/var/log/spoole")
