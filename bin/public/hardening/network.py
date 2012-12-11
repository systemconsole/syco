#!/usr/bin/env python
'''
Apply network settings from var/hardening/config.cfg - part of the hardening.

WARNING
---------------------------------------------------
This script should not be executed on a server acting as a router or gateway.
All traffic going through the host will be blocked.

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
from socket import gethostname

import app
from general import x
from config import general
from scopen import scOpen


def setup_network():
	'''
    Help kernel to prevent certain kinds of attacks

    '''
	app.print_verbose("Setup network (Settings from CIS benchmark)")

	setup_kernel()
	disable_ip6_support()
	configure_resolv_conf()
	configure_localhost()
	restart_network()


def setup_kernel():
    app.print_verbose("Help kernel to prevent certain kinds of attacks")
    config = ConfigParser.SafeConfigParser()
    config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)

    # Harden network config
    for setting in config.options('network'):
        scOpen("/etc/sysctl.conf").replace_add(
        	"^" + setting + ".*$", config.get('network', setting)
        )

    # Flush settings.
    x("/sbin/sysctl -w net.ipv4.route.flush=1")
    x("/sbin/sysctl -w net.ipv6.route.flush=1")


def disable_ip6_support():
  app.print_verbose("Disable IP6 support")
  modprobe = scOpen("/etc/modprobe.d/syco.conf")
  modprobe.replace_add("^options ipv6.*",    "options ipv6 disable=1")
  modprobe.replace_add("^alias net-pf-10 off$", "alias net-pf-10 off")

  network = scOpen("/etc/sysconfig/network")
  network.replace_add("^NETWORKING_IPV6=.*$", "NETWORKING_IPV6=no")


def configure_resolv_conf():
  app.print_verbose("Configure /etc/resolv.conf")
  resolv = scOpen("/etc/resolv.conf")
  resolv.replace_add("domain.*", "domain " + general.get_resolv_domain())
  resolv.replace_add("search.*", "search " + general.get_resolv_search())


def configure_localhost():
  app.print_verbose("Configure /etc/hosts")
  localhost =  (
  	"127.0.0.1" +
  	" %s.%s" % (gethostname(), general.get_resolv_domain()) +
  	" localhost.localdomain localhost %s" % gethostname()
  )
  scOpen("/etc/hosts").replace_add("127.0.0.1.*", localhost)


def restart_network():
	x("service network restart")
