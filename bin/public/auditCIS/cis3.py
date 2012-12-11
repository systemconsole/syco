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

from utils import x, assert_contains

#
print_header("3. Special Purpose Services")

#
print_header("3.1 Set Daemon umask (Scored)")
check_equal(
    "grep umask /etc/sysconfig/init",
    "umask 027"
)

#
print_header("3.2 Remove X Windows (Scored)")
# Original CIS test
# check_equal(
#     'grep "^id:" /etc/inittab',
#     "id:3:initdefault"
# )
# Syco hardened servers use this.
check_equal(
    'grep "^\~\~\:S\:wait\:\/sbin\/sulogin" /etc/inittab',
    "~~:S:wait:/sbin/sulogin"
)

result = x('yum grouplist "X Window System"')
max_lines = len(result)
assert_contains(result[max_lines-3], "Available Groups:")
assert_contains(result[max_lines-2], "  X Window System")
assert_contains(result[max_lines-1], "Done")

#
print_header("3.3 Disable Avahi Server (Scored)")
check_equal(
    "rpm -q avahi",
    "package avahi is not installed"
)
check_empty("chkconfig --list | grep avahi")

#
print_header("3.4 Disable Print Server - CUPS (Not Scored)")
check_equal(
    "rpm -q cups",
    "package cups is not installed"
)
check_empty("chkconfig --list | grep cups")

#
print_header("3.5 Remove DHCP Server (Scored)")
check_equal(
    "rpm -q dhcp",
    "package dhcp is not installed"
)
check_empty("chkconfig --list | grep dhcp")

#
print_header("3.6 Configure Network Time Protocol (NTP) (Scored)")
# Original CIS looks for
# restrict default kod nomodify notrap nopeer noquery
check_equal(
    'grep "restrict default" /etc/ntp.conf',
    "restrict default ignore"
)

# Original CIS looks for
# restrict default kod nomodify notrap nopeer noquery
check_equal(
    'grep "restrict -6 default" /etc/ntp.conf',
    "restrict -6 default ignore"
)

#
print_header("3.7 Remove LDAP (Not Scored)")
print_info("Syco uses LDAP.")

#
print_header("3.8 Disable NFS and RPC (Not Scored)")
check_equal("rpm -q nfslock", "package nfslock is not installed")
check_equal("rpm -q rpcgssd", "package rpcgssd is not installed")
check_equal("rpm -q rpcbind", "package rpcbind is not installed")
check_equal("rpm -q rpcidmapd", "package rpcidmapd is not installed")
check_equal("rpm -q rpcsvcgssd", "package rpcsvcgssd is not installed")
check_empty("chkconfig --list | grep nfslock")
check_empty("chkconfig --list | grep rpcgssd")
check_empty("chkconfig --list | grep rpcbind")
check_empty("chkconfig --list | grep rpcidmapd")
check_empty("chkconfig --list | grep rpcsvcgssd")

#
print_header("3.9 Remove DNS Server (Not Scored)")
check_equal("rpm -q bind", "package bind is not installed")
check_empty("chkconfig --list | grep bind")

#
print_header("3.10 Remove FTP Server (Not Scored)")
check_equal("rpm -q vsftpd", "package vsftpd is not installed")
check_empty("chkconfig --list | grep vsftpd")

#
print_header("3.11 Remove HTTP Server (Not Scored)")
check_equal("rpm -q httpd", "package httpd is not installed")
check_empty("chkconfig --list | grep httpd")

#
print_header("3.12 Remove Dovecot (IMAP and POP3 services) (Not Scored)")
check_equal("rpm -q dovecot", "package dovecot is not installed")
check_empty("chkconfig --list | grep dovecot")

#
print_header("3.13 Remove Samba (Not Scored)")
check_equal("rpm -q samba", "package samba is not installed")
check_empty("chkconfig --list | grep samba")

#
print_header("3.14 Remove HTTP Proxy Server (Not Scored)")
check_equal("rpm -q squid", "package squid is not installed")
check_empty("chkconfig --list | grep squid")

#
print_header("3.15 Remove SNMP Server (Not Scored)")
check_equal("rpm -q net-snmp", "package net-snmp is not installed")
check_empty("chkconfig --list | grep net-snmp")

#
print_header("3.16 Configure Mail Transfer Agent for Local-Only Mode (Scored)")
check_equal(
    'netstat -an | grep LIST | grep ":25[[:space:]]"',
    'tcp        0      0 127.0.0.1:25                0.0.0.0:*                   LISTEN'
)
