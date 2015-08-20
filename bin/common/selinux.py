#!/usr/bin/env python
"""
SELinux help functions

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2015, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

from general import x


def custom_module(path, module):
    module += "-syco"
    te = "%s/%s.te" % (path, module)
    mod = "/tmp/%s.mod" % module
    pp = "/tmp/%s.pp" % module

    x("checkmodule -M -m -o %s %s" % (mod, te))
    x("semodule_package -o %s -m %s" % (pp, mod))
    x("semodule -i %s" % pp)
