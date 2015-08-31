#!/usr/bin/env python
"""
Setup an iptables firewall according to the firewall configuration, general and host-specific.

If for example mysql is installed, port 3306 will be opened for incoming. This
script should be the first script to be exeuted on a new installed server.

This script is based on Oskar Andreassons rc.DMZ.firewall.txt.

Read and learn more about iptables.
http://www.frozentux.net/iptables-tutorial/scripts/rc.DMZ.firewall.txt
http://www.frozentux.net/iptables-tutorial/iptables-tutorial.html
http://manpages.ubuntu.com/manpages/jaunty/man8/iptables.8.html
http://www.cipherdyne.org/psad/
http://security.blogoverflow.com/2011/08/base-rulesets-in-iptables/

"""

__author__ = ["Kristofer Borgstrom", "Daniel Lindh"]
__copyright__ = "Copyright 2015, The System Console project"
__maintainer__ = "Kristofer Borgstrom"
__credits__ = ["Daniel Lindh", "Oskar Andreasson"]
__license__ = "???"
__version__ = "2.0.0"
__status__ = "Test"

import sys


from config import *
from config import get_servers
from general import x
from net import get_hostname
import app
import general
import net
import version


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 5

#Keep track of commands
_commands_obj_reference = None


def build_commands(commands):

    global _commands_obj_reference
    _commands_obj_reference = commands

    commands.add("iptables-clear", iptables_clear, help="Clear all iptables rules.")
    commands.add("iptables-setup", iptables_setup, help="Setup an iptables firewall, customized for installed "
                                                        "services.")


def iptables(args, output=True):
    """
    Execute the iptables shell command.

    """
    x("/sbin/iptables " + args, output=output)


def del_module(name):
    """
    Delete module from IPTABLES_MODULES in /etc/sysconfig/iptables-config

    Plus not needed whitespaces.

    """
    app.print_verbose("Del module " + name)

    # Line 1: Remove all old existing module X
    # Line 2: Only one whitespace between each module
    # Line 3: No whitespaces before last "
    # Line 4: No whitespaces before firstt "
    x('sed -i "/IPTABLES_MODULES=/s/' + name + '\( \|\\"\)/\\1/g;' +
      '/IPTABLES_MODULES=/s/\( \)\+/ /g;' +
      '/IPTABLES_MODULES=/s/ \\"/\\"/g;' +
      '/IPTABLES_MODULES=/s/\\" /\\"/g' +
      '" /etc/sysconfig/iptables-config')
    x("modprobe -r " + name)


def add_module(name):
    """
    Add module to the beginning of IPTABLES_MODULES in /etc/sysconfig/iptables-config

    """
    app.print_verbose("Add module " + name)
    x('sed -i "/IPTABLES_MODULES=/s/\\"/\\"' + name + ' /;' +
      '/IPTABLES_MODULES=/s/ \\"/\\"/g' +
      '" /etc/sysconfig/iptables-config')
    x("modprobe " + name)


def iptables_clear(args):
    """
    Remove all iptables rules.

    """
    app.print_verbose("Clear all iptables rules.")

    # reset the default policies in the filter table.
    iptables("-t filter -P INPUT ACCEPT")
    iptables("-t filter -P FORWARD ACCEPT")
    iptables("-t filter -P OUTPUT ACCEPT")

    # reset the default policies in the nat table.
    iptables("-t nat -P PREROUTING ACCEPT")
    iptables("-t nat -P POSTROUTING ACCEPT")
    iptables("-t nat -P OUTPUT ACCEPT")

    # reset the default policies in the mangle table.
    iptables("-t mangle -P PREROUTING ACCEPT")
    iptables("-t mangle -P POSTROUTING ACCEPT")
    iptables("-t mangle -P INPUT ACCEPT")
    iptables("-t mangle -P OUTPUT ACCEPT")
    iptables("-t mangle -P FORWARD ACCEPT")

    # Flush all chains
    iptables("-F -t filter")
    iptables("-F -t nat")
    iptables("-F -t mangle")

    # Delete all user-defined chains
    iptables("-X -t filter")
    iptables("-X -t nat")
    iptables("-X -t mangle")

    # Zero all counters
    iptables("-Z -t filter")
    iptables("-Z -t nat")
    iptables("-Z -t mangle")


def save():
    """
    Save all current iptables rules to file, so it will be reloaded after reboot.

    """
    app.print_verbose("Save current iptables rules to /etc/sysconfig/iptables.")
    x("/sbin/iptables-save > /etc/sysconfig/iptables")


def iptables_setup(args):
    """
    Setup local iptables firewall
    """
    version_obj = version.Version("iptables-setup", SCRIPT_VERSION)
    version_obj.check_executed()

    # Rules that will be added on all server.
    iptables_clear(args)
    _drop_all()
    create_chains()
    _setup_general_rules()
    setup_ssh_rules()
    setup_dns_resolver_rules()

    add_general_rules()
    add_dynamic_modules()
    add_dynamic_chains()

    save()
    version_obj.mark_executed()


def parse_ip_and_port_setting(settings):
    """
    Parse a string with a comma-separated list of ip and port settings.

    Syntax: [ip|network|host name:]primary-port[->secondary-port]

    For example:
    8.8.8.8:53           # Can be used with allow_tcp_out to allow port 53 to google DNS
    80,443               # Can be used with allow_tcp_in to allow web access to a web server
    80->8080,443->8443   # Can be used with allow_tcp_in to translate incoming port 80 traffic to an internal port 8080
                         # AND 443 to 8443

    Returns a list of dicts with the following possible keys:
    - port
    - host
    - secondary_port
    """

    results = []
    for setting in settings.split(","):
        result = {}

        host_and_ip = setting.split(":")
        #Port is first part assuming if no IP specified
        port_section = host_and_ip[0]
        if len(host_and_ip) == 2:
            #A host name/network/IP was specified
            result['host'] = host_and_ip[0]
            port_section = host_and_ip[1]
        elif len(host_and_ip) > 2:
            app.print_error("Unexpected number of colon separated sections in setting: %s, skipping!" % setting)
            continue

        ports = port_section.split("->")

        result['port'] = ports[0]

        if len(ports) == 2:
            result['secondary_port'] = ports[1]
        elif len(ports) > 2:
            app.print_error("Unexpected number of \"->\" separated port sections in setting: %s, skipping!" % setting)
            continue

        results.append(result)

    return results


def _drop_all():
    app.print_verbose("Drop all traffic to/from/forwarded by this server..")
    iptables("-P INPUT DROP")
    iptables("-P FORWARD DROP")
    iptables("-P OUTPUT DROP")


def setup_syco_chains(device=False):
    """
    Setup input/output/forward chains that are used by all syco installed services.

    This is so it's easier to remove/rebuild iptables rules for a specific
    service. And easier to trace what rules that are used for a specific service.

    """
    app.print_verbose("Create syco input, output, forward chain")

    # Input chain
    iptables("-N syco_input")
    input_device = (" -i " + str(device) if device else "")
    iptables("-A INPUT {0} -p ALL -j syco_input".format(input_device))

    # Output chain
    output_device = (" -o " + str(device) if device else "")
    iptables("-N syco_output")
    iptables("-A OUTPUT {0} -p ALL -j syco_output".format(output_device))

    # Forward chain should not be installed on main firewall.
    # Cant use a single device for forward
    if not device:
        iptables("-N syco_forward")
        iptables("-A FORWARD -p ALL -j syco_forward")

        iptables("-t nat -N syco_nat_postrouting")
        iptables("-t nat -A POSTROUTING -p ALL -j syco_nat_postrouting")


def setup_icmp_chains():
    app.print_verbose("Create ICMP chain.")
    iptables("-N icmp_packets")
    iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type echo-request -j ACCEPT")
    iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type echo-reply -j ACCEPT")
    iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type destination-unreachable -j ACCEPT")
    iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type source-quench -j ACCEPT")
    iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type time-exceeded -j ACCEPT")
    iptables("-A icmp_packets -p ICMP -s 0/0 --icmp-type parameter-problem -j ACCEPT")

    app.print_verbose("Standard icmp_packets from anywhere.")
    iptables("-A INPUT  -p ICMP -j icmp_packets")
    iptables("-A OUTPUT -p ICMP -j icmp_packets")


def setup_multicast_chains():
    app.print_verbose("Create Multicast chain.")
    iptables("-N multicast_packets")
    iptables("-A OUTPUT -p ALL -j multicast_packets")

    multicast_configs = _get_dynamic_firewall_multicast_configs(net.get_hostname())
    if multicast_configs:
        for multicast_config in multicast_configs:
            for rule in multicast_config.get_rules():
                iptables(rule.get_row())
    else:
        #Deny multicast
        iptables("-A multicast_packets -s 224.0.0.0/4 -j DROP")
        iptables("-A multicast_packets -d 224.0.0.0/4 -j DROP")
        iptables("-A multicast_packets -s 0.0.0.0/8 -j DROP")
        iptables("-A multicast_packets -d 0.0.0.0/8 -j DROP")


def add_general_rules():
    #Find general firewall rules in general section of config
    all_general_items = dict(config.general.items("general"))

    #Find and process firewall rules
    for key in all_general_items:
        if key.startswith("fw.host."):
            #Parse rule type by removing the prefix
            rule_type = key[len("fw.host."):]
            #Parse the value(s)
            settings = parse_ip_and_port_setting(all_general_items[key])

            for setting in settings:
                port = setting.get("port")
                host_ = setting.get("host")

                if rule_type.startswith("allow_tcp_out"):
                    iptables(OutboundFirewallRule(ports=[port], dst=host_, protocol="tcp").get_row())
                elif rule_type.startswith("allow_udp_out"):
                    iptables(OutboundFirewallRule(ports=[port], dst=host_, protocol="udp").get_row())
                elif rule_type.startswith("allow_tcp_in"):
                    iptables(InboundFirewallRule(ports=[port], src=host_, protocol="tcp").get_row())
                elif rule_type.startswith("allow_udp_in"):
                    iptables(InboundFirewallRule(ports=[port], src=host_, protocol="udp").get_row())
                else:
                    app.print_verbose("Ignoring unknown firewall rule type: %s" % rule_type)


def add_dynamic_modules():
    firewall_modules = _get_dynamic_firewall_modules(net.get_hostname())

    for module in firewall_modules:
        add_module(module.module_name)


def add_dynamic_chains():

    #Determine all firewall rules for current host
    firewall_rules = _get_dynamic_firewall_rules(net.get_hostname())

    #Create all service chains
    _recreate_service_chains(firewall_rules)

    #Execute all firewall rules
    for rule in firewall_rules:
        iptables(rule.get_row())


def _get_dynamic_firewall_rules(host_name):

    fw_config = _get_dynamic_firewall_config(host_name)
    rules = []

    for row in fw_config:
        if isinstance(row, FirewallRule):
            rules.append(row)

    return rules


def _get_dynamic_firewall_modules(host_name):

    fw_config = _get_dynamic_firewall_config(host_name)
    modules = []

    for row in fw_config:
        if isinstance(row, FirewallModule):
            modules.append(row)

    return modules


def _get_dynamic_firewall_multicast_configs(host_name):

    fw_config = _get_dynamic_firewall_config(host_name)
    multicasts = []

    for row in fw_config:
        if isinstance(row, MulticastConfig):
            multicasts.append(row)

    return multicasts

def _get_dynamic_firewall_config(host_name):

    #Reference to syco.py commands
    global _commands_obj_reference

    all_rules = []
    syco_command_names = config.host(host_name).get_syco_command_names()
    for syco_command in syco_command_names:

        #Find the firewall rules for command
        firewall_rules = _commands_obj_reference.get_command_firewall_config(syco_command)
        if firewall_rules:
            all_rules.extend(firewall_rules)

    return all_rules


def _recreate_service_chains(firewall_rules):
    #Get all service chains and hooks, using a sets to avoid duplicates
    #Chains are unique per service and direction
    #Hooks are unique per service, direction AND protocol
    service_chains = set()
    service_hooks = set()
    for rule in firewall_rules:
        #Ignore syco chains as these have already been created.
        if rule.service == "syco":
            continue
        service_chains.add((rule.service, rule.direction))
        service_hooks.add((rule.service, rule.direction, rule.protocol))

    #Remove existing hooks
    for service_hook in service_hooks:
        iptables("-D syco_{1} -p {2} -j {0}_{1}".format(*service_hook), general.X_OUTPUT_CMD)

    #Remove, flush and create chains
    for service_chain in service_chains:

        iptables("-F {0}_{1}".format(*service_chain), general.X_OUTPUT_CMD)
        iptables("-X {0}_{1}".format(*service_chain), general.X_OUTPUT_CMD)

        #Create chains
        iptables("-N {0}_{1}".format(*service_chain))
    #Add hooks
    for service_hook in service_hooks:
        iptables("-A syco_{1} -p {2} -j {0}_{1}".format(*service_hook))


def create_chains():
    # All drops are going through LOGDROP so it's easy to turn on logging
    # when debugging is needed.
    app.print_verbose("Create LOGDROP chain.")
    iptables("-N LOGDROP")
    iptables("-A LOGDROP -j DROP")

    app.print_verbose("Create allowed tcp chain.")
    iptables("-N allowed_tcp")
    iptables("-A allowed_tcp -p TCP --syn -j ACCEPT")
    iptables("-A allowed_tcp -p TCP -m state --state ESTABLISHED,RELATED -j ACCEPT")
    iptables("-A allowed_tcp -p TCP -j LOGDROP")

    app.print_verbose("Create allowed udp chain.")
    iptables("-N allowed_udp")
    iptables("-A allowed_udp -p UDP -j ACCEPT")
    iptables("-A allowed_udp -p UDP -j LOGDROP")


def _setup_general_rules():
    """
    Rules are in the order of expected volume.

    For example, we expect more ESTABLISHED packages than ICMP packages
    """
    app.print_verbose("From Localhost interface to Localhost IP's.")
    iptables("-A INPUT -p ALL -i lo -s 127.0.0.1 -j ACCEPT")
    iptables("-A OUTPUT -p ALL -o lo -d 127.0.0.1 -j ACCEPT")

    setup_bad_tcp_packets()

    app.print_verbose("Allow all established and related packets incoming from anywhere.")
    iptables("-A INPUT -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT")
    iptables("-A OUTPUT -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT")
    iptables("-A FORWARD -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT")

    setup_syco_chains()
    setup_icmp_chains()
    setup_multicast_chains()

    app.print_verbose("Log weird packets that don't match the above.")
    iptables("-A INPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "
             "'IPT: INPUT packet died: '")
    iptables("-A OUTPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "
             "'IPT: OUTPUT packet died: '")
    iptables("-A FORWARD -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "
             "'IPT: FORWARD packet died: '")

    iptables("-A INPUT -j LOGDROP")
    iptables("-A OUTPUT -j LOGDROP")
    iptables("-A FORWARD -j LOGDROP")


def setup_bad_tcp_packets():
    app.print_verbose("Bad TCP packets we don't want.")

    app.print_verbose("Create bad_tcp_packets chain.")
    iptables("-N bad_tcp_packets")
    iptables("-A bad_tcp_packets -p tcp --tcp-flags SYN,ACK SYN,ACK -m state --state NEW -j REJECT "
             "--reject-with tcp-reset")

    # Force SYN checks
    iptables("-A bad_tcp_packets -p tcp ! --syn -m state --state NEW -j LOG --log-prefix 'IPT: New not syn:'")
    iptables("-A bad_tcp_packets -p tcp ! --syn -m state --state NEW -j LOGDROP")

    # Drop all fragments
    iptables("-A bad_tcp_packets -f -j LOGDROP")

    # Drop XMAS packets
    iptables("-A bad_tcp_packets -p tcp --tcp-flags ALL ALL -j LOGDROP")

    # Drop NULL packets
    iptables("-A bad_tcp_packets -p tcp --tcp-flags ALL NONE -j LOGDROP")

    # Join _after_ creating the new chain
    iptables("-A INPUT   -p tcp -j bad_tcp_packets")
    iptables("-A OUTPUT  -p tcp -j bad_tcp_packets")
    iptables("-A FORWARD -p tcp -j bad_tcp_packets")


def setup_ssh_rules():
    """
    Can SSH to this and any other computer internal and/or external.

    """
    app.print_verbose("Setup ssh INPUT/OUTPUT rule.")
    iptables("-A syco_input -p tcp  -m multiport --dports 22 -j allowed_tcp")
    iptables("-A syco_output -p tcp -m multiport --dports 22 -j allowed_tcp")

# TODO:
#  ################################################################
#  #slow the amount of ssh connections by the same ip address:
#  #wait 60 seconds if 3 times failed to connect
#  ################################################################
#  iptables -I INPUT -p tcp -i eth0 --dport 22 -m state --state NEW -m recent --name sshprobe --set -j ACCEPT
#  iptables -I INPUT -p tcp -i eth0 --dport 22 -m state --state NEW -m recent --name sshprobe --update --seconds 60 \
#           --hitcount 3 --rttl -j LOGDROP


def setup_dns_resolver_rules():
    """
    Allow this server to communicate with all syco approved dns resolvers.

    """
    app.print_verbose("Setup DNS resolver INPUT/OUTPUT rule.")
    for resolver_ip in config.general.get_dns_resolvers():
        if resolver_ip.lower() != "none":
            iptables("-A syco_output -p udp --sport 1024:65535 -d " + resolver_ip +
                     " --dport 53 -m state --state NEW -j allowed_udp")
            iptables("-A syco_output -p tcp --sport 1024:65535 -d " + resolver_ip +
                     " --dport 53 -m state --state NEW -j allowed_tcp")


def del_nfs_chain():
    app.print_verbose("Delete iptables chain for nfs")
    iptables("-D syco_input  -p ALL -j nfs_export", general.X_OUTPUT_CMD)
    iptables("-D syco_output -p ALL -j nfs_export", general.X_OUTPUT_CMD)
    iptables("-F nfs_export", general.X_OUTPUT_CMD)
    iptables("-X nfs_export", general.X_OUTPUT_CMD)


def add_nfs_chain():
    del_nfs_chain()

    app.print_verbose("Add iptables chain for nfs")
    iptables("-N nfs_export")
    iptables("-A syco_input  -p ALL -j nfs_export")
    iptables("-A syco_output -p ALL -j nfs_export")

    iptables("-A nfs_export -m state --state NEW -p tcp --dport 32803 -j allowed_tcp")
    iptables("-A nfs_export -m state --state NEW -p tcp --dport 32769 -j allowed_tcp")
    iptables("-A nfs_export -m state --state NEW -p tcp --dport 892 -j allowed_tcp")
    iptables("-A nfs_export -m state --state NEW -p tcp --dport 875 -j allowed_tcp")
    iptables("-A nfs_export -m state --state NEW -p tcp --dport 662 -j allowed_tcp")
    iptables("-A nfs_export -m state --state NEW -p tcp --dport 2020 -j allowed_tcp")
    iptables("-A nfs_export -m state --state NEW -p tcp --dport 2049 -j allowed_tcp")
    iptables("-A nfs_export -m state --state NEW -p tcp --dport 111 -j allowed_tcp")

    iptables("-A nfs_export -m state --state NEW -p udp --dport 32803 -j allowed_udp")
    iptables("-A nfs_export -m state --state NEW -p udp --dport 32769 -j allowed_udp")
    iptables("-A nfs_export -m state --state NEW -p udp --dport 892 -j allowed_udp")
    iptables("-A nfs_export -m state --state NEW -p udp --dport 875 -j allowed_udp")
    iptables("-A nfs_export -m state --state NEW -p udp --dport 662 -j allowed_udp")
    iptables("-A nfs_export -m state --state NEW -p udp --dport 2020 -j allowed_udp")
    iptables("-A nfs_export -m state --state NEW -p udp --dport 2049 -j allowed_udp")
    iptables("-A nfs_export -m state --state NEW -p udp --dport 111 -j allowed_udp")


def _get_modules(commands_path):
    """
    Return a list of objects representing all available syco modules in specified folder.

    """
    modules=[]
    for module in os.listdir(commands_path):
        if module == '__init__.py' or module[-3:] != '.py':
            continue
        module = module[:-3]

        try:
            obj = getattr(sys.modules[module], "iptables_setup")
            modules.append(obj)
        except AttributeError, e:
            pass

    return modules


class FirewallModule(object):

    module_name = None

    def __init__(self, module_name):
        self.module_name = module_name


class MulticastConfig(object):

    net = None
    protocols = None

    def __init__(self, net, protocols):
        if not isinstance(net, basestring):
            raise ValueError("Expected Multicast network")
        self.net = net

        self.protocols = protocols

    def get_rules(self):
        rules = [
            RawFirewallRule(service="syco", raw="-A multicast_packets -d %s -j ACCEPT" % self.net),
            RawFirewallRule(service="syco", raw="-A multicast_packets -s %s -j ACCEPT" % self.net)
        ]
        if self.protocols:
            for proto in self.protocols:
                rules.append(RawFirewallRule(service="syco", raw="-A syco_input -p %s -j ACCEPT" % proto))
                rules.append(RawFirewallRule(service="syco", raw="-A syco_output -p %s -j ACCEPT" % proto))
        return rules


class FirewallRule(object):

    DIRECTIONS = ["input", "output", "forward"]
    META_ADDRESSES = ["front-ip", "front-net", "back-ip", "back-net", "local-ips", "local-nets"]

    direction = None
    service = None
    ports = []
    output = None
    src = []
    dst = []
    protocol = "tcp"
    raw = None

    def __init__(self, direction=None, service=None, ports=[], src=[], dst=[], raw=None, protocol=None):

        if raw:
            self.raw = raw
            return

        if direction not in self.DIRECTIONS:
            raise ValueError("Unknown direction %s, I only understand: %s" % (direction, ",".join(self.DIRECTIONS)))
        else:
            self.direction = direction

        if service and not isinstance(service, basestring):
            raise ValueError("Expected a string as service parameter")
        elif not service:
            #Default to syco service
            self.service = "syco"
        else:
            self.service = service

        if ports:
            if isinstance(ports, basestring):
                self.ports = [ports]
            else:
                self.ports = ports

        if src:
            self.src = self._parse_addresses(src)

        if dst:
            self.dst = self._parse_addresses(dst)

        if protocol:
            self.protocol = protocol

    def get_row(self):

        if self.raw:
            return self.raw

        return self._build_iptables_command()

    def _parse_addresses(self, addresses):

        if not addresses:
            return []

        if isinstance(addresses, basestring):
            return self._resolve_meta_address(addresses)
        elif isinstance(addresses, list):
            deep_list = [self._resolve_meta_address(addr) for addr in addresses]
            #flatten list, making one list out of lists of lists
            return [item for sublist in deep_list for item in sublist]

    def _resolve_meta_address(self, address):
        hostconf = config.host(net.get_hostname())

        if address == self.META_ADDRESSES[0]:
            return [hostconf.get_front_ip()]
        elif address == self.META_ADDRESSES[1]:
            return [config.general.get_front_subnet()]
        elif address == self.META_ADDRESSES[2]:
            return [hostconf.get_back_ip()]
        elif address == self.META_ADDRESSES[3]:
            return [config.general.get_back_subnet()]
        elif address == self.META_ADDRESSES[4]:
            res = [hostconf.get_front_ip()]
            if config.general.is_back_enabled():
                res.append(hostconf.get_back_ip())
            return res
        elif address == self.META_ADDRESSES[5]:
            res = [config.general.get_front_subnet()]
            if config.general.is_back_enabled():
                res.append(config.general.get_back_subnet())
            return res
        else:
            return [address]

    def _build_iptables_command(self):
        """
        Build the command element by element (might be able to use ":" as wildcard
        for d/sport, and "[+]" for interface wildcard to save some lines

        """

        #Manage service
        if not self.service:
            self.service = "syco"

        #Protocol
        string_chain = "-A %s_%s" % (self.service, self.direction)
        string_protocol = " -p " + self.protocol
        string_source_ip = (" -s " + ",".join(self.src) if self.src else "")
        # Pragmatic solution to --sport/ -m multiport sports choice (instead of more if's) is to always assume multiport
        string_dest_ip = (" -d " + ",".join(self.dst) if self.dst else "")
        string_dest_ports = (" -m multiport --dports=" + ",".join(self.ports) if self.ports else "")
        string_state = " -m state --state NEW"
        string_next_chain = (" -j allowed_%s" % self.protocol)

        command = string_chain + string_protocol + string_source_ip + string_dest_ip + string_dest_ports + \
                  string_state + string_next_chain
        return command


class ForwardFirewallRule(FirewallRule):
    def __init__(self, service=None, ports=[], src=[], dst=[], protocol=None):

        super(self.__class__, self).__init__(direction="forward", service=service, ports=ports, src=src, dst=dst,
                                             protocol=protocol)


class InboundFirewallRule(FirewallRule):
    def __init__(self, service=None, ports=[], src=[], dst=[], protocol=None):

        super(self.__class__, self).__init__(direction="input", service=service, ports=ports, src=src, dst=dst,
                                             protocol=protocol)


class OutboundFirewallRule(FirewallRule):
    def __init__(self, service=None, ports=[], src=[], dst=[], protocol=None):

        super(self.__class__, self).__init__(direction="output", service=service, ports=ports, src=src, dst=dst,
                                             protocol=protocol)


class RawFirewallRule(FirewallRule):
    def __init__(self, service=None, direction=None, raw=None):

        super(self.__class__, self).__init__(direction=direction, service=service, raw=raw)
