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
import re

import net


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
        '''
        Return HostConfig object for hostname.

        '''
        if hostname not in self.hosts:
            self.hosts[hostname] = self.HostConfig(
                hostname, self.etc_path, self.usr_path
            )
        return self.hosts[hostname]

    def get_devices(self):
        '''
        A list of all servers that are defined in install.cfg.

        '''
        servers = self.general.sections()
        servers.remove("general")

        hosts = []
        for hostname in servers:
            if self.host(hostname).is_server() or self.host(hostname).is_switch():
                hosts.append(hostname)

        return sorted(hosts)

    def get_general_fw_config(self):
        conf_dict = {}
        for option in self.general.options("fw"):
            conf_dict[option] = self.general.get("fw", option)

        return conf_dict


    def get_servers(self):
        '''
        A list of all servers that are defined in install.cfg.

        '''
        hosts = [name for name in self.get_devices() if self.host(name).is_server()]
        return sorted(hosts)

    def get_hosts(self):
        '''Get the hostname of all kvm hosts.'''
        hosts = [name for name in self.get_devices() if self.host(name).is_host()]
        return sorted(hosts)

    def get_switches(self):
        '''Get the hostname of all switches.'''
        hosts = [name for name in self.get_devices() if self.host(name).is_switch()]
        return sorted(hosts)


    class SycoConfig(ConfigParser.RawConfigParser):

        def __init__(self, etc_path, usr_path = None):
            ConfigParser.RawConfigParser.__init__(self)

            self.load_general_config_file(etc_path)
            self.load_config_file(etc_path)

        '''
        Load general.cfg if it exists.
        '''

        def load_general_config_file(self, etc_path):
            file_name = etc_path + "general.cfg"

            config_dir = []
            if os.access(file_name, os.F_OK):
                config_dir.append(file_name)

            if len(config_dir) == 1:
                self.read(config_dir[0])
            elif len(config_dir) > 1:
                raise ConfigException(str(len(config_dir)) + " general.cfg found, only one or zero is allowed.",
                                      config_dir)

        def load_config_file(self, etc_path):
            file_name = etc_path + "install.cfg"

            config_dir = []
            if (os.access(file_name, os.F_OK)):
                config_dir.append(file_name)

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

            if (default_value is not None):
                return default_value
            else:
                raise ConfigException(
                    "Can't find value for option '" + option + "' in section '" + section + "' in install.cfg"
                )

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
            return self.get_option("installation.server")

        def get_installation_server_ip(self):
            """The ip of the installation server."""
            return self._get_service_ip("installation")

        def get_front_gateway_ip(self):
            '''The ip of the network gateway.'''
            return self.get_option("front.gateway")

        def is_back_enabled(self):
            if self.get_option("back.disable", "false") == "true":
                return False
            return True

        def get_back_gateway_ip(self):
            '''The ip of the network gateway.'''
            return self.get_option("back.gateway", "")

        def get_front_network(self):
            '''The front network (ie. 10.100.10.0).'''
            return self.get_option("front.network")

        def get_back_network(self):
            '''The back network (ie. 10.100.10.0).'''
            return self.get_option("back.network", "")

        def get_back_subnet(self):
            '''The back subnet (ie. 10.100.10.0/24)'''
            return net.get_network_cidr(
                self.get_back_network(),
                self.get_back_netmask()
            )

        def get_front_netmask(self):
            '''The netmask of the front network.'''
            return self.get_option("front.netmask")

        def get_back_netmask(self):
            '''The netmask of the back network.'''
            return self.get_option("back.netmask", "")

        def get_front_subnet(self):
            '''The back subnet (ie. 10.100.10.0/24)'''
            return net.get_network_cidr(
                self.get_front_network(),
                self.get_front_netmask()
            )

        def get_front_resolver_ip(self):
            '''ip of external dns resolver that are configured on all servers.'''
            return str(self.get_option("front.resolver"))

        def get_external_dns_resolver(self):
            '''todo get_front_dns_resolver_ip'''
            return str(self.get_front_resolver_ip())

        def get_back_resolver_ip(self):
            '''ip of internal dns resolver that are configured on all servers.'''
            return str(self.get_option("back.resolver", ""))

        def get_internal_dns_resolvers(self):
            '''ip list of dns resolvers inside the syco net that are configured on all servers. TODO get_back_dns_resolver_ip'''
            return str(self.get_back_resolver_ip())

        def get_dns_resolvers(self, prefer_back_net=False):
            """
            Ip list of all dns resolvers that are configured on all servers.

            """
            resolvers = []
            if self.get_front_resolver_ip():
                resolvers.append(self.get_front_resolver_ip())

            if self.is_back_enabled() and self.get_back_resolver_ip():
                resolvers.append(self.get_back_resolver_ip())

            if self.get_nameserver_server_ips():
                resolvers.extend(self.get_nameserver_server_ips(prefer_back_net=prefer_back_net))

            return _remove_duplicates_from_list(resolvers)

        def get_first_dns_resolver(self):
            '''ip of primary dns-resolver. TODO remove use get_front/get_back_resolver'''
            return self.get_dns_resolvers()[0]

        def get_resolv_domain(self):
            return self.get_option("resolv.domain")

        def get_resolv_search(self):
            return self.get_option("resolv.search")

        def get_nameserver_server(self):
            return self.get_option("nameserver.server")

        def get_nameserver_server_ip(self, prefer_back_net=False):

            return iter(self.get_nameserver_server_ips(prefer_back_net=prefer_back_net)).next()

        def get_nameserver_server_ips(self, prefer_back_net=False):

            return self._get_service_ips("nameserver", prefer_back_net=prefer_back_net)

        def get_ldap_server(self):
            """The hostname of the ldap server."""
            return self.get_option("ldap.server")

        def get_ldap_server_ip(self):
            return self._get_service_ip("ldap")

        def get_ldap_hostname(self):
            return self.get_option("ldap.hostname")

        def get_ldap_dn(self):
            return self.get_option("ldap.dn")

        def get_monitor_server(self):
            '''The host name of the monitor server.'''
            return self.get_option("monitor.server")

        ''' The IP of the monitor server if specified in the general section OR
            The front.ip of the monitor.server host if the general config does not exist.
        '''

        def get_monitor_server_ip(self):
            return self._get_service_ip("monitor")

        def get_monitor_server_hostname(self):
            return self.get_option("monitor.hostname")

        def get_ntp_server(self):
            '''The hostname of the ntp server.'''
            return self.get_option("ntp.server")

        def get_slave_ntp_server(self):
            '''The hostname of the ntp server.'''
            return self.get_option("ntp.slave.server")

        def get_ntp_server_ip(self):

            return self._get_service_ip("ntp")

        def get_mailrelay_server_ip(self):

            return self._get_service_ip("mailrelay")

        def get_mail_relay_domain_name(self):
            return self.get_option("mailrelay.domain_name")

        def get_mail_relay_server(self):
            '''The hostname of the mail_relay server.'''
            return self.get_option("mailrelay.server", "")

        def get_cert_server(self):
            '''The hostname of the cert server.'''
            return self.get_option("cert.server")

        def get_cert_server_ip(self):
            '''The ip of the cert server.'''
            return self._get_service_ip('cert')

        def get_cert_wild_ca(self):
            '''The hostname of the cert server.'''
            return self.get_option("cert.wild.ca")

        def get_cert_wild_crt(self):
            '''The hostname of the cert server.'''
            return self.get_option("cert.wild.crt")

        def get_cert_wild_key(self):
            '''The hostname of the cert server.'''
            return self.get_option("cert.wild.key")

        def get_mysql_primary_master_ip(self):
            '''IP or hostname for primary mysql server.'''
            return self.get_option("mysql.primary_master_ip")

        def get_mysql_secondary_master_ip(self):
            '''IP or hostname for secondary mysql server.'''
            return self.get_option("mysql.secondary_master_ip")

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

        def get_log_server_hostname1(self):
            return self.get_option("log.hostname1")

        def get_log_server_hostname2(self):
            return self.get_option("log.hostname2")

        def get_subnet(self):
            '''The subnet of the data center'''
            return self.get_option("network.subnet")

        def get_openvpn_network(self):
            '''The network range of the ips givven to openvpn clients.'''
            return str(self.get_option("openvpn.network"))

        def get_openvpn_hostname(self):
            '''The domain name used to access the vpn from internet.'''
            return str(self.get_option("openvpn.hostname"))

        def get_ossec_server(self):
            '''The hostname of the ossec server.'''
            return self.get_option("ossec.server")

        def get_ossec_server_ip(self):
            '''The ip of the ossec server.'''
            return self._get_service_ip("ossec")

        def get_proxy_host(self):
            return self.get_option("http.proxy.host", "")

        def get_proxy_port(self):
            return self.get_option("http.proxy.port", "")

        def _get_service_ip(self, service_name, prefer_back_net=False):
            """
            Get the IP of a service by:
            A) Looking for a general section property called <service-name>.server.ip
            B) Finding front-net (or back-net if specified) IP by host name which is
            retrieved through a function in this class called: get_<service>_server()
            """

            service_ip = self.get_option(service_name + ".server.ip", "")

            if service_ip == "":
                """If IP is not configured, try to get IP from guest configuration for this host"""
                hostname_method = getattr(self, "get_" + service_name + "_server")
                try:
                    service_host_name = hostname_method()
                    if prefer_back_net and self.is_back_enabled():
                        service_ip = self.host(service_host_name).get_back_ip()
                    else:
                        service_ip = self.host(service_host_name).get_front_ip()
                except:
                    pass

            return service_ip

        '''
        Get a list of IPs of a service by:
        A) Looking for a general section property called <service-name>.server.ips
        B) Includes results from _get_service_ip() if <service-name>.server.ips does not exist
        '''
        def _get_service_ips(self, service_name, prefer_back_net=False):

            #Get IPs, split on comma (,) and strip away any whitespace
            service_ips = map(str.strip, self.get_option(service_name + ".server.ips", "").split(","))
            #Fall back to finding one IP
            if not service_ips:
                service_ips = [self._get_service_ip(service_name, prefer_back_net)]

            return service_ips

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
            if hosttype in ['host', 'guest', 'switch', 'firewall', 'template']:
                return hosttype
            else:
                raise Exception("Unknown type {0}".format(hosttype))

        def get_front_interfaces(self):
            '''Get front interfaces for a specific host, as it is defined in install.cfg'''
            return self._get_interfaces("front.interfaces")

        def get_back_interfaces(self):
            '''Get back interfaces for a specific host, as it is defined in install.cfg'''
            return self._get_interfaces("back.interfaces")

        def _get_interfaces(self, interface_name):
            interfaces = self.get_option(interface_name, "").split(",")
            ret = []
            for interface in interfaces:
                if interface.strip() != '':
                    ret.append(interface.strip())
            return ret

        def get_front_ip(self):
            """Get ip for a specific host, as it is defined in install.cfg"""
            return self.get_option("front.ip", "")

        def get_front_mac(self):
            '''Get network mac address for a specific host, as it is defined in install.cfg'''
            return self.get_option("front.mac")

        def get_back_ip(self):
            '''Get ip for a specific host, as it is defined in install.cfg'''
            return self.get_option("back.ip", "")

        def get_back_mac(self):
            '''Get network mac address for a specific host, as it is defined in install.cfg'''
            return self.get_option("back.mac", "")

        def get_any_ip(self):
            ''' Get any ip (front preferred, back second hand, otherwise error'''
            if self.has_option(self.hostname, "front.ip"):
                return(self.get_front_ip())
            elif self.has_option(self.hostname, "back.ip"):
                return(self.get_back_ip())
            else:
                raise Exception("No IP defined for host {0}".format(self.hostname))

        def get_ram(self):
            '''Get the amount of ram in MB that are used for a specific kvm host, as it is defined in install.cfg.'''
            return self.get_option("ram")

        def get_cpu(self):
            '''Get the number of cores that are used for a specific kvm host, as it is defined in install.cfg'''
            return self.get_option("cpu")

        def get_cpu_max(self):
            '''Get the number of cores that are used for a specific kvm host, as it is defined in install.cfg'''
            return self.get_option("cpu_max", "")

        def get_disk_swap_gb(self):
            '''
            Size of the swap partion in GB, as it is defined in install.cfg

            Defaut: 4 GB

            '''
            return self.get_option("disk_swap", "4")

        def get_disk_swap_mb(self):
            '''
            Size of the swap partion in GB, as it is defined in install.cfg

            Defaut: 4096 GB

            '''
            return str(int(self.get_disk_swap_gb()) * 1024)

        def get_disk_var(self):
            '''Get the size of the var partion in GB that are used for a specific kvm host, as it is defined in install.cfg'''
            return self.get_option("disk_var")

        def get_disk_var_gb(self):
            '''
            Size of the /var partion in GB, as it is defined in install.cfg

            Defaut: 10 GB

            '''
            return self.get_option("disk_var", "10")

        def get_disk_var_mb(self):
            '''
            Size of the /var partion in MB, as it is defined in install.cfg

            Defaut: 10240 MB

            '''
            return str(int(self.get_disk_var_gb()) * 1024)

        def get_bind_conf_subdir(self):
            '''
            Gets the relative path to the bind config if any
            The empty default value is required to allow this property to not be defined
            '''
            return str(self.get_option("bind_conf_subdir", ""))

        def get_disk_log_gb(self):
            '''
            Size of the /var/log partion in GB, as it is defined in install.cfg

            Defaut: 4 GB
            '''
            return self.get_option("disk_log", "4")

        def get_disk_log_mb(self):
            '''
            Size of the /var/log partion in MB, as it is defined in install.cfg

            Defaut: 4096 MB
            '''
            return str(int(self.get_disk_log_gb()) * 1024)

        def get_disk_extra_lvm_gb(self):
            '''
            Get the extra empty size to use on the LVM physical group in GB.

            This is used for a specific kvm host, if it needs to extend or snapshot
            an existing volume group. Defined in install.cfg

            '''
            return self.get_option("disk_extra_lvm", 0)

        def get_total_disk_gb(self):
            '''Total size of all partions, the size of the lvm volume on the host.'''
            return str(
                int(self.get_disk_swap_gb()) +
                int(self.get_disk_var_gb()) +
                int(self.get_disk_log_gb()) +
                int(self.get_disk_extra_lvm_gb()) +
                4 + # /
                1 + # /home
                1 + # /var/tmp
                1 + # /var/log/audit
                1 + # /tmp
                1   # some extra free space if any LVM partion needs to be resized.
            )

        def get_total_disk_mb(self):
            '''Total size of all volumes/partions, the size of the lvm volume on the host.'''
            return str(int(self.get_total_disk_gb()) * 1024)

        def get_boot_device(self, default_device = None):
            '''Get the device name on which the installation will be performed.'''
            return self.get_option("boot_device", default_device)

        def get_vol_group(self, default_vol_group = "VolGroup00"):
            '''Get the volume group name on which the installation will be performed.'''
            return self.get_option("vol_group", default_vol_group)

        def _get_template(self):
            '''
            Get the template name that is used

            Default name is host.

            '''
            return self.get_option("use", 'host')

        def _get_template_commands(self, verbose):
            '''
            Get all commands from the template that this profile is associated with.

            '''
            return self._get_commands_from_host(self._get_template(), verbose)

        def is_server(self):
            '''
            Return true if HostConfig is a valid physical device/server.

            Ie. not a template and not General.

            '''
            return (self.is_host() or self.is_guest() or
                    self.is_firewall())

        def is_host(self):
            return self.get_type() == "host"

        def is_guest(self):
            return self.get_type() == "guest"

        def is_switch(self):
            return self.get_type() == "switch"

        def is_firewall(self):
            return self.get_type() == "firewall"

        def is_template(self):
            return self.get_type() == "template"

        def get_syco_command_names(self):
            """
            Get name of all syco commands for this host excluding all arguments etc.
            """

            syco_command_names = []
            commands = self.get_commands()
            for command in commands:
                #Assume second word is the command name
                split_commands = command.split(" ")
                if len(split_commands) < 1:
                    app.print_verbose("Did not understand command: %s, skipping" % command)
                    continue
                elif split_commands[0].lower() == "syco":
                    if len(split_commands) < 2:
                        app.print_verbose("Did not understand syco command: %s, skipping" % command)
                        continue
                else:
                    #This is not a syco command, ignoring it.
                    continue

                #else, this is a syco command and arg[1] should be the name of the command
                syco_command_names.append(split_commands[1])

            return syco_command_names
        def has_guests(self):
            if (self.has_section(self.hostname)):
                for option, value in self.items(self.hostname):
                    if ("guest" in option):
                        return True
            return False

        def get_commands(self, verbose = False):
            '''Get all commands that should be executed on a host'''
            commands = self._get_template_commands(verbose)
            commands += self._get_commands_from_host(self.hostname, verbose)

            ret_commands = []
            for option, value in sorted(commands):
                ret_commands.append(value)

            return ret_commands

        def has_command_re(self, cmd_pattern):
            '''
            Check if cmd will or has been executed on the host.

            '''
            prog = re.compile(cmd_pattern)
            for command in self.get_commands():
                if prog.search(command) != None:
                    return True
            return False

        def _get_commands_from_host(self, hostname, verbose):
            commands = []
            if (self.has_section(hostname)):
                for option, value in self.items(hostname):
                    option = option.lower()
                    if "command" in option:
                        if (verbose):
                            value += " -v"
                        commands.append([option, value])
            return commands

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

def get_switches():
    return config.get_switches()

def _remove_duplicates_from_list(list):
    seen = set()
    seen_add = seen.add
    return [x for x in list if not (x in seen or seen_add(x))]

def get_devices():
    return config.get_devices()
