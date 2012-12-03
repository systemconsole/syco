#!/usr/bin/env python
'''
Audit the server according to CIS Redhat Linux 6 Benchmark v1.1.0.

This script will not do any changes on the server, only do lookups to see
if everything is properly configured. It's also coded to have as few
dependencies as possible from the rest of syco. So it in a future version can
be distribured without syco.

READ MORE
https://benchmarks.cisecurity.org/tools2/linux/CIS_Red_Hat_Enterprise_Linux_6_Benchmark_v1.1.0.pdf

EXAMPLES
syco audit-cis     -- Check if server is CIS compliant.
syco audit-cis -v  -- Display verbose info text for warnings.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from utils import print_total_status

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


def build_commands(commands):
    commands.add("audit-cis", audit_cis, help="Audit the server according to CIS Redhat Linux 6 Benchmark v1.1.0.")


def audit_cis(args):
    print("Audit the server according to CIS Redhat Linux 6 Benchmark v1.1.0.")
    print("version: %d\n" % SCRIPT_VERSION)

    import cis1
    import cis2
    import cis3
    import cis4
    import cis5
    import cis6
    import cis7
    import cis8
    import cis9
    import cisBonus

    # Print status for the last section.
    print_total_status()
