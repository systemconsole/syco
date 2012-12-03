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
print_header("7. User Accounts and Environment")

#
print_header("7.1 Set Shadow Password Suite Parameters (/etc/login.defs)")

#
print_header("7.1.1 Set Password Expiration Days (Scored)")
check_equal(
    "grep ^PASS_MAX_DAYS /etc/login.defs",
    "PASS_MAX_DAYS\t90"
)

check_empty(
    'awk -F: \'($3 > 0) {print $1}\' /etc/passwd | xargs -I {} ' +
    'chage --list {}|' +
    'grep "^Maximum number of days between password change"|'+
    'grep -v ": 99$"'
)

#
print_header("7.1.2 Set Password Change Minimum Number of Days (Scored)")
check_equal(
    "grep ^PASS_MIN_DAYS /etc/login.defs",
    "PASS_MIN_DAYS\t7"
)

check_empty(
    'awk -F: \'($3 > 0) {print $1}\' /etc/passwd | xargs -I {} ' +
    'chage --list {}|' +
    'grep "^Miniumum number of days between password change"|'+
    'grep -v ": 7$"'
)

#
print_header("7.1.3 Set Password Expiring Warning Days (Scored)")
check_equal(
    "grep ^PASS_WARN_AGE /etc/login.defs",
    "PASS_WARN_AGE\t14"
)

check_empty("""
    awk -F: '($3 > 0) {print $1}' /etc/passwd | xargs -I {} \
    chage --list {}| \
    grep "^Number of days of warning before password expires"| \
    grep -v ": 7$"
""")

#
print_header("7.2 Disable System Accounts (Scored)")
check_empty("""
    awk -F: '($1!="root" && $1!="sync" && $1!="shutdown" && $1!="halt" && $3<500 && $7!="/sbin/nologin") {print}' /etc/passwd
""")

#
print_header("7.3 Set Default Group for root Account (Scored)")
check_equal(
    "grep ^root /etc/passwd | cut -f4 -d:",
    "0"
)

#
print_header("7.4 Set Default umask for Users (Scored)")
check_equal_re("grep 'umask 077' /etc/bashrc",    ".*umask 077.*")
check_equal_re("grep 'umask 077' /etc/profile",   ".*umask 077.*")
check_equal_re("grep 'umask 077' /etc/csh.cshrc", ".*umask 077.*")

#
print_header("7.5 Lock Inactive User Accounts (Scored)")
check_equal(
    "useradd -D | grep INACTIVE",
    "INACTIVE=35"
)
