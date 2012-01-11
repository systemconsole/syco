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

class ConfigException(Exception):
  '''
  Raised when their is an invalid number of install.cfg

  '''
  pass

class Config(object):
  etc_path = None
  usr_path = None
  hosts = {}

  def __init__(self, etc_path, usr_path = None):
    self.etc_path = etc_path
    self.usr_path = usr_path
    self.general = self.GeneralConfig(etc_path, usr_path)

  def host(self, hostname):
    if hostname not in self.hosts:
      self.hosts[hostname] = self.HostConfig(hostname,
                                             self.etc_path, self.usr_path)
    return self.hosts[hostname]

  def get_servers(self):
    '''A list of all servers that are defined in install.cfg.'''
    servers = self.general.sections()
    servers.remove("general")
    return servers

  def get_hosts(self):
    '''Get the hostname of all kvm hosts.'''
    hosts = []

    for hostname in self.get_servers():
      if self.host(hostname).is_host():
        hosts.append(hostname)
    return sorted(hosts)

  class SycoConfig(ConfigParser.RawConfigParser):

    def __init__(self, etc_path, usr_path = None):
      ConfigParser.RawConfigParser.__init__(self)

      self.load_config_file(etc_path, usr_path)

    def load_config_file(self, etc_path, usr_path):
      file_name = etc_path + "install.cfg"

      config_dir = []
      if (os.access(file_name, os.F_OK)):
        config_dir.append(file_name)

      if (usr_path):
        for dir in os.listdir(usr_path):
          if (os.access(usr_path + dir + "/etc/install.cfg", os.F_OK)):
            config_dir.append(usr_path + dir + "/etc/install.cfg")

      if (len(config_dir) == 0):
        raise ConfigException("No install.cfg found.")
      elif (len(config_dir) > 1):
        raise ConfigException(str(len(config_dir)) + " install.cfg found, only one is allowed.", config_dir)
      else:
        self.read(config_dir[0])

    def get_option(self, section, option, default_value = None):
      '''
      Get an option from the install.cfg file.

      '''
      value = None

      if (self.has_section(section)):
        if (self.has_option(section, option)):
          value = str(self.get(section, option))
          if value.lower() == "none":
            return None
          else:
            return value

      if (default_value):
        return default_value
      else:
        raise ConfigException(
          "Can't find value for option '" + option + "' in section '" + section + "' in install.cfg")

    def get_option_list(self, section):
      '''
      Get an option from the install.cfg file.

      '''
      value = {}

      if (self.has_section(section)):
        for option in self.options(section):
          value[option] = self.get(section, option)
           
        return value
      else:
        raise ConfigException(
          "Can't find section '" + section + "' in install.cfg") 
        
  class GeneralConfig(SycoConfig):
    '''
    Access functions for the [general] part in the install.cfg.

    '''
    etc_path = None
    usr_path = None

    def __init__(self, etc_path, usr_path):
      Config.SycoConfig.__init__(self, etc_path, usr_path)
      self.etc_path = etc_path
      self.usr_path = usr_path

    def get_option(self, option, default_value = None):
      return Config.SycoConfig.get_option(self, "general", option, default_value)

    def host(self, hostname):
      return Config.HostConfig(hostname, self.etc_path, self.usr_path)

    def get_installation_server(self):
      '''The hostname of the installation server.'''
      return self.get_option("installation_server")

    def get_installation_server_ip(self):
      '''The ip of the installation server.'''
      return self.host(self.get_installation_server()).get_back_ip()

    def get_front_gateway_ip(self):
      '''The ip of the network gateway.'''
      return self.get_option("front.gateway")

    def get_back_gateway_ip(self):
      '''The ip of the network gateway.'''
      return self.get_option("back.gateway")

    def get_front_netmask(self):
      '''The netmask of the front network.'''
      return self.get_option("front.netmask")

    def get_back_netmask(self):
      '''The netmask of the back network.'''
      return self.get_option("back.netmask")

    def get_front_resolver_ip(self):
      '''ip of external dns resolver that are configured on all servers.'''
      return str(self.get_option("front.resolver"))

    def get_external_dns_resolver(self):
      '''todo get_front_dns_resolver_ip'''
      return str(self.get_front_resolver_ip())

    def get_back_resolver_ip(self):
      '''ip of internal dns resolver that are configured on all servers.'''
      return str(self.get_option("back.resolver"))

    def get_internal_dns_resolvers(self):
      '''ip list of dns resolvers inside the syco net that are configured on all servers. TODO get_back_dns_resolver_ip'''
      return str(self.get_back_resolver_ip())

    def get_dns_resolvers(self, limiter=" "):
      '''
      Ip list of all dns resolvers that are configured on all servers.

      '''
      resolvers = str(self.get_front_resolver_ip() + " " + self.get_back_resolver_ip())

      if (limiter != " "):
        resolvers = resolvers.replace(' ', limiter)
      return resolvers

    def get_first_dns_resolver(self):
      '''ip of primary dns-resolver. TODO remove use get_front/get_back_resolver'''
      return self.get_dns_resolvers().split(None, 1)[0]

    def get_resolv_domain(self):
      return self.get_option("resolv.domain")

    def get_resolv_search(self):
      return self.get_option("resolv.search")

    def get_ldap_server(self):
      '''The hostname of the ldap server.'''
      return self.get_option("ldap.server")

    def get_ldap_server_ip(self):
      return self.host(self.get_ldap_server()).get_back_ip()

    def get_ldap_hostname(self):
      return self.get_option("ldap.hostname")

    def get_ldap_dn(self):
      return self.get_option("ldap.dn")

    def get_ntp_server(self):
      '''The hostname of the ntp server.'''
      return self.get_option("ntp.server")

    def get_ntp_server_ip(self):
      return self.host(self.get_ntp_server()).get_back_ip()

    def get_mail_relay_domain_name(self):
      return self.get_option("mail_relay.domain_name")

    def get_cert_server(self):
      '''The hostname of the cert server.'''
      return self.get_option("cert.server")

    def get_cert_server_ip(self):
      '''The ip of the cert server.'''
      return self.host(self.get_cert_server()).get_back_ip()

    def get_cert_wild_ca(self):
      '''The hostname of the cert server.'''
      return self.get_option("cert.wild.ca")

    def get_cert_wild_crt(self):
      '''The hostname of the cert server.'''
      return self.get_option("cert.wild.crt")
      
    def get_cert_wild_key(self):
      '''The hostname of the cert server.'''
      return self.get_option("cert.wild.key")            

    def get_mysql_primary_master(self):
      return self.get_option("mysql.primary_master")

    def get_mysql_primary_master_ip(self):
      '''IP or hostname for primary mysql server.'''
      return self.host(self.get_mysql_primary_master()).get_back_ip()

    def get_mysql_secondary_master(self):
      return self.get_option("mysql.secondary_master")

    def get_mysql_secondary_master_ip(self):
      '''IP or hostname for primary mysql server.'''
      return self.host(self.get_mysql_secondary_master()).get_back_ip()

    def get_country_name(self):
      return self.get_option("country_name")

    def get_state(self):
      return self.get_option("state")

    def get_locality(self):
      return self.get_option("locality")

    def get_organization_name(self):
      return self.get_option("organization_name")

    def get_organizational_unit_name(self):
      return self.get_option("organizational_unit_name")

    def get_admin_email(self):
      return self.get_option("admin_email")

    def get_dns_range(self):
      return self.get_option("dns.range")
    
    def get_dns_localnet(self):
      return self.get_option("dns.localnet")
    
    def get_dns_forward1(self):
      return self.get_option("dns.forward1")
    
    def get_dns_forward2(self):
      return self.get_option("dns.forward2")
    
    def get_dns_ipmaster(self):
      return self.get_option("dns.ipmaster")

    def get_dns_ipslave(self):
      return self.get_option("dns.ipslave")
    
    def get_dns_data_center(self):
      return self.get_option("dns.data_center")

    def get_dns_zones(self):
      '''
      Get zones used for dns in install.cfg file
      
      '''
      return self.get_option_list('zone')

  class HostConfig(SycoConfig):
    '''
    Access functions for the hosts in the install.cfg.

    '''

    hostname = None

    def __init__(self, hostname, etc_path, usr_path):
      Config.SycoConfig.__init__(self, etc_path, usr_path)
      self.hostname = hostname

    def get_option(self, option, default_value = None):
      return Config.SycoConfig.get_option(self, self.hostname, option, default_value)

    def get_type(self):
      '''Get ip for a specific host, as it is defined in install.cfg'''
      hosttype = self.get_option("type").lower()
      if hosttype in ['host', 'guest']:
        return hosttype

    def get_front_ip(self):
      '''Get ip for a specific host, as it is defined in install.cfg'''
      return self.get_option("front.ip")

    def get_front_mac(self):
      '''Get network mac address for a specific host, as it is defined in install.cfg'''
      return self.get_option("front.mac")

    def get_back_ip(self):
      '''Get ip for a specific host, as it is defined in install.cfg'''
      return self.get_option("back.ip")

    def get_back_mac(self):
      '''Get network mac address for a specific host, as it is defined in install.cfg'''
      return self.get_option("back.mac")

    def get_ram(self):
      '''Get the amount of ram in MB that are used for a specific kvm host, as it is defined in install.cfg.'''
      return self.get_option("ram")

    def get_cpu(self):
      '''Get the number of cores that are used for a specific kvm host, as it is defined in install.cfg'''
      return self.get_option("cpu")

    def get_disk_swap_gb(self):
      '''Get the size of the swap partion in GB that are used for a specific kvm host, as it is defined in install.cfg'''
      return self.get_option("disk_swap", "4")

    def get_disk_swap_mb(self):
      '''Get the size of the swap partion in MB that are used for a specific kvm host, as it is defined in install.cfg'''
      return str(int(self.get_disk_swap_gb()) * 1024)

    def get_disk_var(self):
      '''Get the size of the var partion in GB that are used for a specific kvm host, as it is defined in install.cfg'''
      return self.get_option("disk_var")

    def get_disk_var_gb(self):
      '''Get the size of the var partion in GB that are used for a specific kvm host, as it is defined in install.cfg'''
      return self.get_option("disk_var")

    def get_disk_var_mb(self):
      '''Get the size of the var partion in MB that are used for a specific kvm host, as it is defined in install.cfg'''
      return str(int(self.get_disk_var_gb()) * 1024)

    def get_total_disk_gb(self):
      '''Total size of all volumes/partions, the size of the lvm volume on the host.'''
      return str(int(self.get_disk_var_gb()) + 16)

    def get_total_disk_mb(self):
      '''Total size of all volumes/partions, the size of the lvm volume on the host.'''
      return str(int(self.get_total_disk_gb()) * 1000)

    def get_boot_device(self, default_device = None):
      '''Get the device name on which the installation will be performed.'''
      return self.get_option("boot_device", default_device)

    def is_host(self):
      return self.get_type() == "host"

    def has_guests(self):
      if (self.has_section(self.hostname)):
        for option, value in self.items(self.hostname):
          if ("guest" in option):
            return True
      return False

    def get_commands(self, verbose = False):
      '''Get all commands that should be executed on a host'''
      commands = []

      if (self.has_section(self.hostname)):
        for option, value in self.items(self.hostname):
          option = option.lower()
          if "command" in option:
            if (verbose):
              value += " -v"
            commands.append([option, value])

      ret_commands = []
      for option, value in sorted(commands):
        ret_commands.append(value)

      return ret_commands

    def get_guests(self):
      '''Get the hostname of all guests that should be installed on the kvm host name.'''
      guests = []

      if (self.has_section(self.hostname)):
        for option, value in self.items(self.hostname):
          if "guest" in option:
            guests.append(value)

      return sorted(guests)

    def get_backup_pathes(self):
      '''Get all pathes that should be backuped.'''
      path = []

      # Always backup thease
      path.append("/etc/")

      # Backup urls from install.cfg
      if (self.has_section(self.hostname)):
        for option, value in self.items(self.hostname):
          if "backup" in option:
            path.append(value)

      return path

#
# Setup module members
#
config = None
general = None
def load(etc_path, usr_path = None):
  global config, general
  config = Config(etc_path, usr_path)
  general = config.general

def host(hostname):
  global config
  return config.host(hostname)

def get_servers():
  return config.get_servers()

def get_hosts():
  return config.get_hosts()
