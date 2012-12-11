#!/usr/bin/env python
'''
Disable services listed in hardening/config.cfg - part of the hardening.

Turn of autostart of services that are not used, and don't need to be used on a
default centos server.

Which services are autostarted
chkconfig  --list |grep on

Which services are autostarted in level 3
chkconfig --list |grep "3:on" |awk '{print $1}' |sort

What status has the services, started/stopped?
/sbin/service --status-all

For more info:
http://www.sonoracomm.com/support/18-support/114-minimal-svcs
http://www.imminentweb.com/technologies/centos-disable-unneeded-services-boot-time
http://magazine.redhat.com/2007/03/09/understanding-your-red-hat-enterprise-linux-daemons/

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
import os

import app
from general import x


def disable_services():
    config = ConfigParser.SafeConfigParser()
    config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)
    for service in config.options('service'):
      app.print_verbose("Disabling service %s " % service)
      if os.path.exists('/etc/xinetd.d/%s'  % service):
        disable_service(service)


def disable_service(name):
  '''
  Disable autostartup of a service and stop the service

  '''
  result = x('chkconfig --list |grep "3:on" |awk \'{print $1}\' |grep ' + name)
  if (result[0][:-1] == name):
    x("chkconfig %s off" % name)

  result = x('service %s status' % name)[0][:-1]
  if ("stopped" not in result and "not running" not in result):
    x("/sbin/service %s stop" % name)
