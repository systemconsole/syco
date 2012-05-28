#!/usr/bin/env python
'''
Remove packages listed in hardening/config.cfg - part of the hardening.

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import app
import config
import scOpen
from general import x


def setup_general():
    customize_shell()
    disable_usb()
    forward_root_mail()
    yum_update()


def customize_shell():
    app.print_verbose("Customize shell")

    app.print_verbose("  Add Date And Time To History Output")
    scOpen("/etc/bashrc").replace(
        "^export HISTTIMEFORMAT=.*$",
        "export HISTTIMEFORMAT=\"%h/%d - %H:%M:%S \""
    )

    app.print_verbose("  Add Color To Grep")
    root = scOpen("/root/.bash_profile")
    root.replace("^export GREP_COLOR=.*$",   "export GREP_COLOR='1;32'")
    root.replace("^export GREP_OPTIONS=.*$", "export GREP_OPTIONS=--color=auto")

    skel = scOpen("/etc/skel/.bash_profile")
    skel.replace("^export GREP_COLOR=.*$",   "export GREP_COLOR='1;32'")
    skel.replace("^export GREP_OPTIONS=.*$", "export GREP_OPTIONS=--color=auto")


def disable_usb():
    # Currently need usb dvd reader for installation.
    return
    app.print_verbose("Disable usb")
    scOpen("/etc/modprobe.d/syco.conf").replace(
        "^blacklist usb-storage$", "blacklist usb-storage"
    )
    x("chcon system_u:object_r:modules_conf_t:s0 /etc/modprobe.d/syco.conf")


def forward_root_mail():
    app.print_verbose("Forward all root email to " + config.general.get_admin_email())
    scOpen("/etc/aliases").replace(
        ".*root[:].*", "root:     " + config.general.get_admin_email()
    )
    x("/usr/bin/newaliases")


def yum_update():
  app.print_verbose("Update with yum")
  x("yum update -y")
