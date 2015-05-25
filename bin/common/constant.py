#!/usr/bin/env python
'''
Contains global functions and settings.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import sys

# The version of the syco script.
version = "0.3.1"
parser = ''

# SYCO root folder.
SYCO_PATH = "/opt/syco/"

# Scripts that should be availble in public repos.
SYCO_PUBLIC_PATH = SYCO_PATH + "bin/public/"

# Scripts that should only be available in private repos.
SYCO_USR_PATH = SYCO_PATH + "usr/"

# Etc (config) files.
SYCO_ETC_PATH = SYCO_PATH + "etc/"

# Var (config) files.
SYCO_VAR_PATH = SYCO_PATH + "var/"

# Files (rpm etc.) that should be installed by syco, are temporary stored here.
INSTALL_DIR = SYCO_PATH + "installtemp/"

# All passwords used by syco are stored in this enrypted file.
PASSWORD_STORE_PATH = SYCO_PATH + "etc/passwordstore"

# When a general username is required.
SERVER_ADMIN_NAME = "syco"

# String codes affecting output to shell.
BOLD = "\033[1m"
RESET = "\033[0;0m"

if __name__ == '__main__':
    print "SYCO_PATH: " + SYCO_PATH
    print "SYCO_PUBLIC_PATH: " + SYCO_PUBLIC_PATH
    print "SYCO_USR_PATH: " + SYCO_USR_PATH
