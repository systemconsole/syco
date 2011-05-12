#!/usr/bin/env python
'''
Holding values defiend in install.cfg.

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
import os

import app

class SycoConfig(ConfigParser.RawConfigParser):

  class SycoConfigException(Exception):
    '''
    Raised when their is an invalid number of install.cfg
    '''

  def __init__(self):
    ConfigParser.RawConfigParser.__init__(self)

    config_dir = []
    if (os.access(app.SYCO_ETC_PATH + "install.cfg", os.F_OK)):
      config_dir.append(app.SYCO_ETC_PATH + "install.cfg")
    for dir in os.listdir(app.SYCO_USR_PATH):
      if (os.access(app.SYCO_USR_PATH + dir + "/etc/install.cfg", os.F_OK)):
        config_dir.append(app.SYCO_USR_PATH + dir + "/etc/install.cfg")

    if (len(config_dir) == 0):
      raise self.SycoConfigException("No install.cfg found.")
    elif (len(config_dir) > 1):
      raise self.SycoConfigException(str(len(config_dir)) + " install.cfg found, only one is allowed.", config_dir)
    else:
      self.read(config_dir[0])

  def get_option(self, section, option):
    '''
    Get an option from the install.cfg file.

    '''
    if (self.has_section(section)):
      if (self.has_option(section, option)):
        return self.get(section, option)
      else:
        raise Exception("Can't find option '" + option + "' in section '" + section + "' in install.cfg")
    else:
      raise Exception("Can't find section '" + section + "' in install.cfg")

  def get_country_name(self):
    return self.get_option("general", "country_name")

  def get_state(self):
    return self.get_option("general", "state")

  def get_locality(self):
    return self.get_option("general", "locality")

  def get_organization_name(self):
    return self.get_option("general", "organization_name")

  def get_organizational_unit_name(self):
    return self.get_option("general", "organizational_unit_name")

  def get_admin_email(self):
    return self.get_option("general", "admin_email")

  def get_ldap_server(self):
    '''The hostname of the ldap server.'''
    return self.get_option("general", "ldap.server")

  def get_ldap_server_ip(self):
    return app.get_ip(self.get_ldap_server())

  def get_ldap_hostname(self):
    return self.get_option("general", "ldap.hostname")

  def get_ldap_dn(self):
    return self.get_option("general", "ldap.dn")

  def get_internal_dns_resolvers():
    '''ip list of dns resolvers inside the syco net that are configured on all servers.'''
    dns_resolver = config.get_option("general", "dns.internal_resolvers")

  def get_external_dns_resolver():
    '''ip of external dns resolver that are configured on all servers.'''
    dns_resolver = config.get_option("general", "dns.external_resolver").split(None, 1)[0]

  def get_dns_resolvers():
    '''ip list of all dns resolvers that are configured on all servers.'''
    dns_resolver = get_internal_dns_resolvers() + " " + get_external_dns_resolvers()

  def get_first_dns_resolver():
    '''ip of primary dns-resolver.'''
    return get_dns_resolvers().split(None, 1)[0]

app.config.get_first_dns_resolver()