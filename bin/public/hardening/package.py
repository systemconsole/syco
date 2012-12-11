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


import ConfigParser

from general import x
import app
import install


def install_packages():
    '''
    Should also match all kickstarts.

    This function needs to be here because we sometimes (virtual hosts) install
    syco without kickstart files.

    '''
    # The same packages that are defined in our kickstarts.
    x(
        "yum install -y acpid cronie-anacron coreutils e2fsprogs git grub lvm2 man " +
        "mlocate nspr nss nss-util openssh openssh-clients openssh-server " +
        "policycoreutils-python rpm wget yum yum-presto"
    )


def remove_packages():
    '''
    Script for removing yum packages on server
    '''
    app.print_verbose("Remove yum packages.")
    config = ConfigParser.SafeConfigParser()
    config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)
    for package in config.options('package'):
        app.print_verbose("  Remove %s." % package)
        install.rpm_remove(package)

def packages():
    remove_packages()
    install_packages()
