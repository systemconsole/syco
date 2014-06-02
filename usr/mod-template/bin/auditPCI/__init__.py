#!/usr/bin/env python
'''
Audit the server according to PCI DSS.

This script will not do any changes on the server, only do lookups to see
if everything is properly configured. It's also coded to have as few
dependencies as possible from the rest of syco. So it in a future version can
be distribured without syco.

EXAMPLES
syco audit-pci     -- Check if server is PCI DSS compliant.
syco audit-pci -v  -- Display verbose info text for warnings.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2013, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    commands.add("audit-pci", audit_pci, help="Audit the server according to PCI DSS.")


def audit_pci(args):
    print("Audit the server according to PCI DSS.")
    print("Script version: %d\n" % SCRIPT_VERSION)

    #import pciNetworkDevices
    import pciPlatforms
    import pciApplications
    import pciFirewalls

    # push_to_github()


if __name__ == "__main__":
    audit_pci(None)
