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
import app

#
print_header("8 Warning Banners")

#
print_header("8.1 Set Warning Banner for Standard Login Services (Scored)")
check_empty("diff %s/hardening/issue.net /etc/motd" % app.SYCO_VAR_PATH)
check_empty("diff %s/hardening/issue.net /etc/issue" % app.SYCO_VAR_PATH)
check_empty("diff %s/hardening/issue.net /etc/issue.net" % app.SYCO_VAR_PATH)

check_equal('stat -c "%a %u %g" /etc/motd | egrep "644 0 0"', "644 0 0")
check_equal('stat -c "%a %u %g" /etc/issue | egrep "644 0 0"', "644 0 0")
check_equal('stat -c "%a %u %g" /etc/issue.net | egrep "644 0 0"', "644 0 0")

#
print_header("8.2 Remove OS Information from Login Warning Banners (Scored)")
check_empty("egrep '(\\\\v|\\\\r|\\\\m|\\\\s)' /etc/issue")
check_empty("egrep '(\\\\v|\\\\r|\\\\m|\\\\s)' /etc/motd")
check_empty("egrep '(\\\\v|\\\\r|\\\\m|\\\\s)' /etc/issue.net")

#
print_header("8.3 Set GNOME Warning Banner (Not Scored)")
print_info("Not using gnome.")
