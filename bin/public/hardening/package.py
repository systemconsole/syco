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

import app
import install


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
