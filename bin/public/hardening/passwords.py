#!/usr/bin/env python
'''
Harden password policy - part of the hardening.

- Set login shell to /dev/null for system accounts
- Disabling accounts with empty passwords
- Locking accounts in shadow with !! instead of ! or *
- Set password expire
- Set password complexity

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import fileinput
import sys

from general import x
from scopen import scOpen
import app


def harden_password():
    app.print_verbose("Harden password")

    #
    # Set login shell to /dev/null
    #
    app.print_verbose("CIS 7.2 Disable System Accounts (Scored)")
    app.print_verbose("  Set login shell to '/sbin/nologin' for system accounts")
    for line in open("/etc/passwd"):
        userid = int(line.split(':')[2]);
        username = line.split(':')[0];

        if userid > 0 and userid <= 499:
            x("/usr/sbin/usermod -L -s /sbin/nologin %s" % username)

    #
    # Disable users with empty passwords in the shadow file.
    #
    app.print_verbose("Disable users with empty passwords in the shadow file.")
    shadow = open("/etc/shadow")
    for line in shadow:
        shadowpass = line.split(':')[1]
        shadowuser = line.split(':')[0]
        if shadowpass.strip() == "":
            x("usermod -L -s /dev/null " + shadowuser)
            app.print_verbose("Diable user %s with empty password." %  shadowuser)

    #
    # Modify locked accounts in /etc/shadow by replacing * and ! to !!
    #
    app.print_verbose(
        "Modify locked accounts in /etc/shadow by replacing * and ! to !!"
    )
    replaceShadow("/etc/shadow", ":!:",":!!:")
    replaceShadow("/etc/shadow", ":*:",":!!:")

    #
    # Set account expiration parameters on active accounts
    #
    app.print_verbose("Set account expiration parameters on active accounts")
    login_defs = scOpen("/etc/login.defs")

    #
    app.print_verbose("CIS 7.2.1 Set Password Expiration Days")
    login_defs.replace_add("^PASS_MAX_DAYS.*", "PASS_MAX_DAYS\t90")
    x("awk -F: '($3 > 0) {print $1}' /etc/passwd | xargs -I {} chage --maxdays 99 {}")

    #
    app.print_verbose("CIS 7.2.2 Set Password Change Minimum Number of Days")
    login_defs.replace_add("^PASS_MIN_DAYS.*", "PASS_MIN_DAYS\t7")
    x("awk -F: '($3 > 0) {print $1}' /etc/passwd | xargs -I {} chage --mindays 7 {}")

    #
    app.print_verbose("CIS 7.2.3 Set Password Expiring Warning Days")
    login_defs.replace_add("^PASS_WARN_AGE.*", "PASS_WARN_AGE\t14")
    x("awk -F: '($3 > 0) {print $1}' /etc/passwd | xargs -I {} chage --warndays 7 {}")

    #
    login_defs.replace_add("^PASS_MIN_LEN.*",  "PASS_MIN_LEN\t9")

    #
    app.print_verbose("CIS 7.5 Lock Inactive User Accounts")
    x("useradd -D -f 35")

    #
    # authconfig needs to be done before any other changes to system-auth
    # or it will restore old settings.
    app.print_verbose("CIS 6.3.5 Upgrade Password Hashing Algorithm to SHA-512")
    x("authconfig --passalgo=sha512 --update --disablefingerprint")

    #
    # Set pam to enforce complex passwords
    # 3 tries to change password (retry=3)
    # 9 entries mini lenght (minlen=9)
    # 3 entries must differ from last password (difok=3)
    # 1 lover case letter miminmum (lcredit=1)
    # 1 upper case letter minimum (ucredit=1)
    # 1 digits minimu (dcredit=1)
    # 2 other caracter (ocredit=2)
    #
    app.print_verbose("CIS 6.3.1 Set Password Creation Requirement Parameters Using pam_cracklib")
    scOpen("/etc/pam.d/system-auth").replace(
        "^password.*requisite.*pam_cracklib.so.*",
        "password    requisite     pam_cracklib.so try_first_pass retry=3 " +
        "minlen=14,dcredit=-1,ucredit=-1,ocredit=-2,lcredit=-1,difok=3"
    )

    #
    # Lock accounts after 5 failed login attempts. Admin must unlock account.
    #

    #
    app.print_verbose("CIS 6.3.3 Set Lockout for Failed Password Attempts")
    scOpen("/etc/pam.d/system-auth").replace(
        "^auth.*required.*pam_tally.so.*",
        "auth\trequired\tpam_tally2.so onerr=fail deny=5"
    )

    #
    app.print_verbose("CIS 6.3.6 Limit Password Reuse")
    scOpen("/etc/pam.d/system-auth").add_to_end_of_line(
        "password.*pam_unix.so",
        "remember=5"
    )

    # Disbling su for user not in the wheel group
    app.print_verbose("CIS 6.5 Restrict Access to the su Command")
    scOpen("/etc/pam.d/su").replace(
        ".*auth.*required.*pam_wheel.so.*",
        "auth        required    pam_wheel.so use_uid"
    )


def replaceShadow(file,searchExp,replaceExp):
    for line in fileinput.input(file,inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)
