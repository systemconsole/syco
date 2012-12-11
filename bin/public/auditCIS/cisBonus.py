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


import ConfigParser

from utils import check_empty, check_equal, check_equal_re, check_equals, check_not_empty, check_return_code, print_header, view_output, print_warning, print_info
import app


def verify_network():
    '''
    Verify that the network config settings in the hardning config file has
    been applied.

    Not a CIS test.

    '''
    print_header("10 BONUS - Verify network settings")

    config = ConfigParser.SafeConfigParser()
    config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)
    counter = 0
    for setting in config.options('network'):
        counter += 1
        print_header(
            "10.{0} Verify network settings - {1}".format(
            counter, config.get('network', setting))
        )
        check_not_empty("grep %s /etc/sysctl.conf" % config.get('network', setting))


def verify_ssh():
    '''
    Verify that all ssh settings has been applied.

    Not a CIS test.

    '''
    #
    print_header("11 BONUS - Verify ssh settings")

    #
    print_header("11.1 BONUS - Verify ssh settings")
    config = ConfigParser.SafeConfigParser()
    config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)
    counter = 0
    for setting in config.options('ssh'):
        counter += 1
        print_header("11.%s Verify ssh settings - %s" %
            (counter, config.get('ssh', setting)))

        check_not_empty("grep %s /etc/ssh/ssh_config" % config.get('ssh', setting))

    #
    print_header("11.2 BONUS - Verify ssh settings")
    counter = 0
    for setting in config.options('sshd'):
        counter += 1

        print_header("11.%s Verify sshd settings - %s" %
            (counter, config.get('sshd', setting)))

        check_not_empty("grep %s /etc/ssh/sshd_config" % config.get('sshd', setting))

#
# Tests to execute on import
#
verify_network()
verify_ssh()
