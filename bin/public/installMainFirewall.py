#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Installs iptables to act as main firewall/router for traffic to a server location.

Input arguments:
    A configuration file. Example located in
        syco-private/var/firewall/fw-example.cfg

Expected behavior (and recommended command order):

    #Optional
    install-firewall-interfaces: Bonds 2 or 4 interfaces in mode 1, and attaches
        bridges with correct IP-config.

    install-firewall-aliases:    Creates an alias (i.e ifcfg-br1:n file) in the
        network-scripts folder for every public IP in the config file.

    install-main-firewall:   Set up a firewall by modifying nat/filter
        table in the kernel. See code comments. All existing iptables
        rules will be flushed!

Recommended reading
    "man iptables"
    http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch14_:_Linux_Firewalls_Using_iptables
    http://wiki.centos.org/HowTos/Network/IPTables


"""

__author__ = "Kristofer Borgström, Elis Kullberg"
__copyright__ = "Copyright 2015, The System Console project"
__maintainer__ = "Kristofer Borgström"
__credits__ = ["Daniel Lindh, Mattias Hemmingsson"]
__version__ = "1.0.0"
__status__ = "Test"

import ConfigParser
import iptables as syco_iptables
from scopen import scOpen

from general import x
import app
import general
import install
import net
import os
import version
import netUtils
import re

iptables = "/sbin/iptables"

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    commands.add("install-firewall-interfaces", install_interfaces, "[config-file]",
                 help="Bonds main firewall interfaces sets up bridges ready for more public aliases")
    commands.add("install-firewall-aliases",    install_aliases,    "[config-file]",
                 help="Installs aliases for public IPs")
    commands.add("install-main-firewall",       install_main_firewall,   "[config-file]",
                 help="Install iptables-based main firewall/router")


def install_interfaces(args):
    """
    Bonds 2 or 4 interfaces in mode 1, and attaches bridges with correct network-config.
    """
    version_obj = version.Version("InstallInterfaces", SCRIPT_VERSION)
    version_obj.check_executed()

    app.print_verbose("Setting up firewall interfaces")
    (c, conf) = _parse_config_file(args[1])

    setup_interfaces(c)
    app.print_verbose("Interfaces set up successfully")

    version_obj.mark_executed


def install_aliases(args):
    """
    Loops through the config files and adds a interface-alias in the external
    bridge (i.e ifcfg-br1:n) for every external IP. Ensures only
    relevant aliases are created.
    """
    version_obj = version.Version("InstallAliases", SCRIPT_VERSION)
    version_obj.check_executed()

    app.print_verbose("Setting up firewall aliases")
    (c, conf) = _parse_config_file(args[1])
    setup_aliases(conf)
    app.print_verbose("Aliases set up successfully")

    version_obj.mark_executed


def install_main_firewall(args):
    """
    Installs an iptables-based rule set. Then flushes currently loaded iptables.
    Then applies general input/output/forwarding filter rules, then applies
    specific filter/DNAT rules on a per-host basis according to the config file.
    Finally adds SNAT for all traffic to external IPs. Finally saves the config,
    i.e makes it stateful.

    """
    app.print_verbose("Installing firewall")
    version_obj = version.Version("InstallMainFirewall", SCRIPT_VERSION)
    version_obj.check_executed()

    (c, conf) = _parse_config_file(args[1])
    load_modules()
    flush_tables()

    # Setup global & input/output chain filtering
    setup_global_filters()
    setup_io_filters(c)
    setup_temp_io_filters(c)

    # Setup DNAT/SNAT & forward chain filtering
    setup_forwarding(c, conf)
    process_allow_rules(c, conf)
    setup_source_nat(c)

    # Close global filters log packets that fell through
    close_global_filters()

    # Make changes stateful
    save_settings()
    app.print_verbose("Done - safe surfing!")

    version_obj.mark_executed


def allow_established():
    """
    This part makes the firewall stateful by allowing the kernel to track
    sessions, and allow all traffic that is marked as part on a previously
    established session. I.e all filter checks are for NEW sessions only.

    """

    allow_tcp_in(state="ESTABLISHED,RELATED")
    allow_tcp_out(state="ESTABLISHED,RELATED")
    allow_udp_in(state="ESTABLISHED,RELATED")
    allow_udp_out(state="ESTABLISHED,RELATED")

    forward_tcp(state="ESTABLISHED,RELATED")
    forward_udp(state="ESTABLISHED,RELATED")


def flush_tables():
    """
    Difference between this and service iptables stop is that kernel mdoules
    aren't unloaded, so that chains can be re-built easily.

    """
    x("sysctl -w net.ipv4.ip_forward=1")

    # reset the default policies in the filter table.
    x(iptables + " -P INPUT ACCEPT")
    x(iptables + " -P FORWARD ACCEPT")
    x(iptables + " -P OUTPUT ACCEPT")

    # reset the default policies in the nat table.
    x(iptables + " -t nat -P PREROUTING ACCEPT")
    x(iptables + " -t nat -P POSTROUTING ACCEPT")
    x(iptables + " -t nat -P OUTPUT ACCEPT")

    # reset the default policies in the mangle table.
    x(iptables + " -t mangle -P PREROUTING ACCEPT")
    x(iptables + " -t mangle -P POSTROUTING ACCEPT")
    x(iptables + " -t mangle -P INPUT ACCEPT")
    x(iptables + " -t mangle -P OUTPUT ACCEPT")
    x(iptables + " -t mangle -P FORWARD ACCEPT")

    # Flush all chains
    x(iptables + " -F -t filter")
    x(iptables + " -F -t nat")
    x(iptables + " -F -t mangle")

    # Delete all user-defined chains
    x(iptables + " -X -t filter")
    x(iptables + " -X -t nat")
    x(iptables + " -X -t mangle")

    # Zero all counters
    x(iptables + " -Z -t filter")
    x(iptables + " -Z -t nat")
    x(iptables + " -Z -t mangle")


def load_modules():
    """
    Load relevant kernel modules
    """

    #TODO: determine if this is required for FTP
    #app.print_verbose("Load modules")
    #x("modprobe nf_conntrack") # Probably not needed
    #x("modprobe nf_conntrack_ftp ports=21") # Needed
    #x("modprobe nf_nat_ftp ports=21") # Needed


def _parse_config_file(filepath):
    """
    This method parses the separate configuration file.

    Return value: An ConfigBranch-object containing a tree-structure of all
                  configuration for easy access.

    """
    app.print_verbose("Parsing configuration file")
    conf = ConfigParser.ConfigParser()
    conf.read(filepath)
    c = ConfigBranch(conf)
    return c, conf


def setup_global_filters():
    syco_iptables.create_chains()


def setup_source_nat(c):
    """
    Configures the postrouting chain of the NAT-table. This part is quite
    frustrating to "wrap your head around". The two final rules are needed
    hosts to access other hosts on their external IP, for which snat is needed
    back into the DMZ. However, output from the firewall itself should be
    skipped (or hosts without default routes will be inaccessible from firewall).

    WARNING: SNAT is not so simple anymore.

    """
    app.print_verbose("Configuring postrouting")

    # Snat to internet
    snat_all(dest_interface=c.interfaces.internet_interface, snat_ip=c.interfaces.internet_ip)

    #
    # A server in the DMZ access another DMZ server on the external ip.
    # SNAT traffic coming into dmz interface and same site (not same subnet
    # i.e longer netmask) and going back into dmz
    #
    # IE: Without this rule, when host1 accesses host2 on external ip, the tcp
    #     traffic will be returned on internal ip, and not go through firewall.
    #     And host1 will drop the tcp packages, because it expects them to come
    #     from firewall.
    snat_all(source_ip = c.interfaces.dmz_ip+c.interfaces.dmz_netmask, dest_interface=c.interfaces.dmz_interface,
             snat_ip=c.interfaces.dmz_ip)


def close_global_filters():
    # Log all packages reaching this. We shouldn't get them.
    x(iptables + ' -A INPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix '
                 '"IPT INPUT packet died: "')
    x(iptables + ' -A OUTPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix '
                 '"IPT OUTPUT packet died: "')
    x(iptables + ' -A FORWARD -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix '
                 '"IPT FORWARD packet died: "')

    # Default policies
    x(iptables + " -P INPUT DROP")
    x(iptables + " -P OUTPUT DROP")
    x(iptables + " -P FORWARD DROP")


def save_settings():
    """
    Save iptables and ip-routing statefully

    """
    app.print_verbose("Saving iptables chain")
    x("/sbin/service iptables save")

    # Persist kernel settings
    general.set_config_property(
        "/etc/sysctl.conf",
        "net.ipv4.ip_forward.*", "net.ipv4.ip_forward = 1", False
    )
    general.set_config_property2("/etc/modprobe.d/syco.conf", "alias bond0 bonding")
    general.set_config_property2("/etc/modprobe.d/syco.conf", "alias bond1 bonding")

    # Make modules stateful
    cfg = scOpen("/etc/sysconfig/iptables-config")
    cfg.replace(
        'IPTABLES_MODULES.*',
        'IPTABLES_MODULES="nf_conntrack nf_nat_ftp"'
    )

    # Set module parameters
    # TODO Remove if kernel figures these out anyway
    # x("rm -f /etc/modprobe.d/syco-iptables")
    # cfg = scOpen("/etc/modprobe.d/syco-iptables")
    # cfg.add('modprobe nf_conntrack ports=21')
    # cfg.add('modprobe nf_nat_ftp ports=21')


def setup_forwarding(c,conf):
    """
    Setup general forwarding settings that apply to all hosts.
    Some sections are removed "provisionally", hence commented out.

    """

    app.print_verbose("Setting up forward chain")
    # DMZ are allowed to access DMZ
    forward_all(source_interface=c.interfaces.dmz_interface, dest_interface=c.interfaces.dmz_interface)


def process_allow_rules(c, conf):
    """
    Parse through config file and set up forwarding for all hosts that should
    be accessible on a public IP, or need access to external services on a
    specific port. Options for access type are port and protocol. Also handles
    DNAT.

    """
    app.print_verbose("Processing allow rules")

    for server in conf.sections():
        all_rule = False
        if server.lower() == "all":
            all_rule = True

        for option in conf.options(server):

            #Only process allow rules further here.
            if option.startswith("allow_"):
                #Retrieve and parse settings for processing allow rules.
                #If dmz and internet_ip settings don't exist, that's ok at this point
                try:
                    dmz_ip = conf.get(server, "dmz_ip")
                except ConfigParser.NoOptionError:
                    pass
                try:
                    internet_ip = conf.get(server, "internet_ip")
                except ConfigParser.NoOptionError:
                    pass

                if all_rule:
                    #DMZ and intenet IP makes no sense for "all", make sure it's not set
                    dmz_ip = False
                    internet_ip = False

                #Check if this config section is the firewall itself by checking dmz of firewall matches that of this
                # section
                server_is_fw = False
                if c.interfaces.dmz_ip == dmz_ip:
                    server_is_fw = True

                settings = syco_iptables.parse_ip_and_port_setting(conf.get(server, option))
                for setting in settings:
                    port = setting.get("port")
                    host = setting.get("host")
                    secondary_port = setting.get("secondary_port")

                    if option.startswith("allow_tcp_out"):

                        if all_rule or server_is_fw:
                            allow_tcp_out(dest_interface=c.interfaces.internet_interface, dest_ports=port,
                                          dest_ip=host)

                        if not server_is_fw:
                            forward_tcp(source_interface=c.interfaces.dmz_interface, source_ip=dmz_ip,
                                        dest_ports=port, dest_ip=host)

                            # If host has a internet_ip it should leave the firewall on that
                            # ip or else use the default public ip for the fw, which is
                            # defined in postrouting().
                            if internet_ip:
                                snat_tcp(
                                    source_ip=dmz_ip,
                                    dest_interface=c.interfaces.internet_interface,
                                    dest_ports=port,
                                    snat_ip=internet_ip
                                )

                    elif option.startswith("allow_udp_out"):

                        if all_rule or server_is_fw:
                            allow_udp_out(dest_interface=c.interfaces.internet_interface, dest_ports=port,
                                          dest_ip=setting.get('host'))

                        if not server_is_fw:
                            forward_udp(source_interface=c.interfaces.dmz_interface, source_ip=dmz_ip,
                                        dest_ports=port, dest_ip=host)

                            # If host has a internet_ip it should leave the firewall on that
                            # ip or else use the default public ip for the fw, which is
                            # defined in postrouting().
                            if internet_ip:
                                snat_udp(
                                    source_ip=dmz_ip,
                                    dest_interface=c.interfaces.internet_interface,
                                    dest_ports=port,
                                    snat_ip=internet_ip
                                )

                    elif option.startswith("allow_tcp_in"):

                        if all_rule:
                            app.print_error("allow_tcp_in rule not valid in context 'all', ignoring")
                            continue

                        #If there is a secondary port, it needs to be the target of forward rule and
                        # be included in the DNAT target
                        f_port = port
                        dnat_target = dmz_ip

                        if secondary_port:
                            f_port = secondary_port
                            dnat_target += ":" + f_port

                        forward_tcp(dest_interface=c.interfaces.dmz_interface, dest_ip=dmz_ip,
                                    dest_ports=f_port, source_ip=host)

                        dnat_tcp(dest_ip=internet_ip, dest_ports=port,
                                 dnat_ip=dnat_target, source_ip=host)

                    elif option.startswith("allow_udp_in"):
                        if all_rule:
                            app.print_error("allow_udp_in rule not valid in context 'all', ignoring")
                            continue

                        #If there is a secondary port, it needs to be the target of forward rule and
                        # be included in the DNAT target
                        f_port = port
                        dnat_target = dmz_ip

                        if secondary_port:
                            f_port = secondary_port
                            dnat_target += ":" + f_port

                        forward_udp(dest_interface=c.interfaces.dmz_interface, dest_ip=dmz_ip,
                                    dest_ports=f_port, source_ip=host)
                        dnat_udp(dest_ip=internet_ip, dest_ports=port, dnat_ip=dnat_target,
                                 source_ip=host)

                    elif option == "allow_icmp_in" and dmz_ip:
                        forward_icmp(dest_interface=c.interfaces.dmz_interface, dest_ip=dmz_ip)
                    elif option == "allow_icmp_out" and dmz_ip:
                        forward_icmp(source_interface=c.interfaces.dmz_interface, source_ip=dmz_ip)


def setup_aliases(conf):
    """
    Loops through the config files and adds a interface-alias in the external
    bridge (i.e ifcfg-br1:n) for every external IP. Ensures only relevant
    aliases are created.

    """
    delete_aliases(conf)

    app.print_verbose("Setting up IP aliases")
    install.package("python-ipaddr")
    import ipaddr

    inet_network = ipaddr.IPv4Network(
        conf.get("interfaces", "internet_ip") +
        conf.get("interfaces", "internet_netmask")
    )
    inet_interface = conf.get("interfaces", "internet_interface")
    inet_interface_broadcast = str(inet_network.broadcast)
    inet_interface_netmask = str(inet_network.netmask)

    for section in conf.sections():
        if (conf.has_option(section, "internet_ip")) and (section != "interfaces"):
            # Text in alias-file
            alias_text = """
                            DEVICE=%s
                            IPADDR=%s
                            TYPE=Ethernet
                            BOOTPROTO=none
                            BROADCAST=%s
                            NETMASK=%s
                            ONBOOT=yes
                            """ % (
                inet_interface + ":" + (conf.get(section, "internet_ip")).split(".")[3],
                conf.get(section, "internet_ip"),
                inet_interface_broadcast,
                inet_interface_netmask)

            # Filename for alias file
            alias_file_name = "/etc/sysconfig/network-scripts/ifcfg-" + inet_interface + ":" + \
                              (conf.get(section, "internet_ip")).split(".")[3]
            x("echo '%s' > %s" % (alias_text, alias_file_name))

    x("service network restart")


def delete_aliases(conf):
    """
    Delete all ifcfg files created by this script before.

    """
    inet_interface = conf.get("interfaces", "internet_interface")
    app.print_verbose("Remove aliases for device {0}".format(inet_interface))

    path = "/etc/sysconfig/network-scripts/"
    dir_list = os.listdir(path)
    for file_name in sorted(dir_list):
        if file_name.startswith('ifcfg-{0}:'.format(inet_interface)):
            full_path = path + file_name
            x('ifdown %s' % file_name)
            os.unlink(full_path)


def setup_interfaces(c):
    """
    Bonds ethernet-interfaces in mode 1, and adds bonds to a bridge. Supports
    both 2 and 4 NIC machines (even though bonds arent very useful in the
    former type!). Kernel bond aliases are stateful.

    """
    app.print_verbose("Setting up firewall interfaces.")
    install.package("python-ipaddr")

    # Install virtual bridging
    install.package("bridge-utils")

    # Add aliases for bond0/1 so they can be modprobed during runtime
    general.set_config_property2(
        "/etc/modprobe.d/syco.conf", "alias bond0 bonding"
    )
    general.set_config_property2(
        "/etc/modprobe.d/syco.conf", "alias bond1 bonding"
    )

    # Get number of interfaces
    num_of_if = net.num_of_eth_interfaces()

    inet_network = ipaddr.IPv4Network(c.interfaces.internet_ip +
                                      c.interfaces.internet_netmask)
    dmz_network = ipaddr.IPv4Network(c.interfaces.dmz_ip
     + c.interfaces.dmz_netmask)

    front_ip = c.interfaces.internet_ip
    front_netmask = str(inet_network.netmask)
    front_gw = c.interfaces.internet_gateway
    front_resolver = c.dns.primary_dns.replace(" ", "").split(',')[0]

    back_ip = c.interfaces.dmz_ip
    back_netmask = str(dmz_network.netmask)
    back_gw = False
    back_resolver = False

    if num_of_if >= 4:
        # Setup back-net
        netUtils.setup_bridge("br0", back_ip, back_netmask, back_gw, back_resolver)
        netUtils.setup_bond("bond0", "br0")
        netUtils.setup_eth("eth0", "bond0")
        netUtils.setup_eth("eth1", "bond0")

        # _setup front-net
        netUtils.setup_bridge("br1", front_ip, front_netmask, front_gw, front_resolver)
        netUtils.setup_bond("bond1", "br1")
        netUtils.setup_eth("eth2", "bond1")
        netUtils.setup_eth("eth3", "bond1")
    elif num_of_if == 2:
        # Setup back-net
        netUtils.setup_bridge("br0", back_ip, back_netmask, back_gw, back_resolver)
        netUtils.setup_bond("bond0", "br0")
        netUtils.setup_eth("eth0", "bond0")

        # _setup front-net
        netUtils.setup_bridge("br1", front_ip, front_netmask, front_gw, front_resolver)
        netUtils.setup_bond("bond1", "br1")
        netUtils.setup_eth("eth1", "bond1")
    else:
        raise Exception("Wrong amount of network interfaces (2 or >= 4 allowed): " + str(num_of_if))

    x("service network restart")


def setup_io_filters(c):
    """
    Rules that affect the firewall's INPUT/OUTPUT chains. I.e they affect
    communication with a firewall IP as origin/destination.  Rules are shared
    with the iptables-setup script active in all other machines. However,
    syco-chains for dmz-services are only allowed on the DMZ interface.

    """
    app.print_verbose("Setting up input and output chain")

    # General io chains
    syco_iptables.setup_bad_tcp_packets()
    allow_established()

    # DMZ-side input/output chains
    syco_iptables.setup_syco_chains(c.interfaces.dmz_interface)
    syco_iptables.add_service_chains()
    syco_iptables.setup_icmp_chains()
    syco_iptables.setup_installation_server_rules()


def setup_temp_io_filters(c):
    """
    Optimally, firewall should not be able to be accessed/access anything via
    input/output chains on the internet interface. However, a few exceptions
    are needed initially.

    """
    # Temporary rules to allow SSH in/out
    # Only ssh from bounce server at a later date
    allow_tcp_in(dest_ports="22", dest_ip=c.interfaces.dmz_ip)



#
# Helper functions and classes
#


### FILTER TABLE, INPUT CHAIN ####


def allow_all_in(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                 dest_ports=False, dest_interface=False, state=False):
    allow_tcp_in(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                 next_chain="allowed_tcp")
    allow_udp_in(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                 next_chain="allowed_udp")
    allow_icmp_in(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                  next_chain="icmp_packets")


def allow_tcp_in(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                 dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_tcp"):
    allow_command = _build_iptables_command(table, source_ip, dest_ip, "INPUT", "tcp", source_interface, source_ports,
                                           dest_ports, dest_interface, state, next_chain)
    x(allow_command)


def allow_udp_in(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                 dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_udp"):
    allow_command = _build_iptables_command(table, source_ip, dest_ip, "INPUT", "udp", source_interface, source_ports,
                                            dest_ports, dest_interface, state, next_chain)
    x(allow_command)


def allow_icmp_in(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                  dest_ports=False, dest_interface=False, state=False, next_chain="icmp_packets"):
    allow_command = _build_iptables_command(table, source_ip, dest_ip, "INPUT", "ICMP", source_interface, source_ports,
                                            dest_ports, dest_interface, state, next_chain)
    x(allow_command)

### FILTER TABLE, OUTPUT CHAIN ###


def allow_all_out(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                  dest_ports=False, dest_interface=False, state=False, next_chain=False):
    allow_tcp_out(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                  next_chain="allowed_tcp")
    allow_udp_out(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                  next_chain="allowed_udp")
    allow_icmp_out(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                   next_chain="icmp_packets")


def allow_tcp_out(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                  dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_tcp"):
    allow_command = _build_iptables_command(table, source_ip, dest_ip, "OUTPUT", "tcp",source_interface, source_ports,
                                            dest_ports, dest_interface, state, next_chain)
    x(allow_command)


def allow_udp_out(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                  dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_udp"):
    allow_command = _build_iptables_command(table, source_ip, dest_ip, "OUTPUT", "udp",source_interface, source_ports,
                                            dest_ports, dest_interface, state, next_chain)
    x(allow_command)


def allow_icmp_out(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                   dest_ports=False, dest_interface=False, state=False, next_chain="icmp_packets"):
    allow_command = _build_iptables_command(table, source_ip, dest_ip, "OUTPUT", "ICMP",source_interface, source_ports,
                                            dest_ports, dest_interface, state, next_chain)
    x(allow_command)


### FILTER TABLE, FORWARDING CHAIN ####


def forward_all(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                dest_ports=False, dest_interface=False, state=False, next_chain=False):
    forward_tcp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                next_chain="allowed_tcp")
    forward_udp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                next_chain="allowed_udp")
    forward_icmp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state,
                 next_chain="icmp_packets")


def forward_tcp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_tcp"):
    forward_command = _build_iptables_command(table, source_ip, dest_ip, "FORWARD", "tcp",source_interface,
                                              source_ports, dest_ports, dest_interface, state, next_chain)
    x(forward_command)


def forward_udp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_udp"):
    forward_command = _build_iptables_command(table, source_ip, dest_ip, "FORWARD", "udp",source_interface,
                                              source_ports, dest_ports, dest_interface, state, next_chain)
    x(forward_command)


def forward_icmp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
                 dest_ports=False, dest_interface=False, state=False, next_chain="icmp_packets"):
    forward_command = _build_iptables_command(table, source_ip, dest_ip, "FORWARD", "ICMP",source_interface,
                                              source_ports, dest_ports, dest_interface, state, next_chain)
    x(forward_command)


### NAT TABLE, PREROUTING CHAIN ###


def dnat_all(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False,
             dest_interface=False, state=False, next_chain="DNAT", dnat_ip=False):
    dnat_tcp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain,
             dnat_ip)
    dnat_udp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain,
             dnat_ip)
    dnat_icmp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain,
              dnat_ip)


def dnat_tcp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False,
             dest_interface=False, state=False, next_chain="DNAT", dnat_ip=False):
    dnat_command = _build_iptables_command("nat", source_ip, dest_ip, "PREROUTING", "tcp", source_interface,
                                           source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)
    x(dnat_command)


def dnat_udp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False,
             dest_interface=False, state=False, next_chain="DNAT", dnat_ip=False):
    dnat_command = _build_iptables_command("nat", source_ip, dest_ip, "PREROUTING", "udp",source_interface,
                                           source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)
    x(dnat_command)


def dnat_icmp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
              dest_ports=False, dest_interface=False, state=False, next_chain="DNAT", dnat_ip=False):
    dnat_command = _build_iptables_command("nat", source_ip, dest_ip, "PREROUTING", "icmp",source_interface,
                                           source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)
    x(dnat_command)


### NAT TABLE, POSTROUTING CHAIN ###


def snat_all(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
             dest_ports=False, dest_interface=False, state=False, next_chain="SNAT", dnat_ip=False, snat_ip=False):
    snat_tcp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain,
             dnat_ip, snat_ip)
    snat_udp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain,
             dnat_ip, snat_ip)
    snat_icmp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain,
              dnat_ip, snat_ip)


def snat_tcp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False,
             dest_interface=False, state=False, next_chain="SNAT", dnat_ip=False, snat_ip=False):
    snat_command = _build_iptables_command("nat", source_ip, dest_ip, "POSTROUTING", "tcp",source_interface,
                                           source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip,snat_ip)
    x(snat_command)


def snat_udp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
             dest_ports=False, dest_interface=False, state=False, next_chain="SNAT", dnat_ip=False, snat_ip=False):
    snat_command = _build_iptables_command("nat", source_ip, dest_ip, "POSTROUTING", "udp", source_interface,
                                           source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip,
                                           snat_ip)
    x(snat_command)


def snat_icmp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False,
              dest_ports=False, dest_interface=False, state=False, next_chain="SNAT", dnat_ip=False, snat_ip=False):
    snat_command = _build_iptables_command("nat", source_ip, dest_ip, "POSTROUTING", "icmp", source_interface,
                                           source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip,
                                           snat_ip)
    x(snat_command)


def _build_iptables_command(table=False, source_ip=False, dest_ip=False, chain=False, protocol=False,
                            source_interface=False, source_ports=False, dest_ports=False, dest_interface=False,
                            state=False, next_chain="ACCEPT", dnat_ip=False, snat_ip=False):
    """
    Build the command element by element (might be able to use ":" as wildcard
    for d/sport, and "[+]" for interface wildcard to save some lines

    """
    string_table = (" -t " + table if table else "")
    string_chain = " -A " + chain
    string_protocol = " -p " + protocol
    string_source_ip = (" -s " + str(source_ip) if source_ip else "")
    # Pragmatic solution to --sport/ -m multiport sports choice (instead of more if's) is to always assume multiport
    string_source_ports = (" -m multiport --sports=" + str(source_ports) if source_ports else "")
    string_source_interface = (" -i " + str(source_interface) if source_interface else "")
    string_dest_ip = (" -d " + str(dest_ip) if dest_ip else "")
    string_dest_ports = (" -m multiport --dports=" + str(dest_ports) if dest_ports else "")
    string_dest_interface = (" -o " + str(dest_interface) if dest_interface else "")
    string_state = (" -m state --state " + str(state) if state else "")
    string_next_chain = (" -j " + next_chain)
    string_dnat_ip = (" --to-destination " + dnat_ip if dnat_ip else "")
    string_snat_ip = (" --to-source " + snat_ip if snat_ip else "")
    command = iptables + string_table + string_chain + string_protocol + string_source_ip + string_source_interface + \
              string_source_ports + string_dest_ip + string_dest_ports + string_dest_interface + string_state + \
              string_next_chain + string_dnat_ip + string_snat_ip
    return command


# TODO: Set a good name and move to a better place
def _set_config_property(file_name, search_exp, replace_exp, add_if_not_exist=True):
    """
    Change or add a config property to a specific value.

    #TODO: Optimize, do more then one change in the file at the same time.
    #TODO: Replace with scOpen??

    """
    if os.path.exists(file_name):
        if replace_exp == None:
            replace_exp = ""

        exist = False
        try:
            shutil.copyfile(file_name, file_name + ".bak")
            r = open(file_name + ".bak", 'r')
            w = open(file_name, 'w')
            for line in r:
                if re.search(search_exp, line):
                    line = re.sub(search_exp, replace_exp, line)
                    exist = True
                w.write(line)

            if exist == False and add_if_not_exist:
                w.write(replace_exp + "\n")
        finally:
            r.close()
            w.close()
            os.remove(file_name + ".bak")
    else:
        w = open(file_name, 'w')
        w.write(replace_exp + "\n")
        w.close()


# TODO: Set a good name and move to a better place
def _set_config_property2(file_name, replace_exp):
    search_exp = r".*" + re.escape(replace_exp) + r".*"
    _set_config_property(file_name, search_exp, replace_exp)


class ConfigBranch(object):
    '''
    Creates a object tree of config file.

    ie.
        self.dns.primary_dns = 8.8.8.8
        self.dns.secondary_dns = 8.8.4.4

    '''
    def __init__(self, Conf):
        for server in Conf.sections():
            setattr(self, server, ConfigLeaf(Conf, server))


class ConfigLeaf(object):
    def __init__(self, Conf, server):
        for option in Conf.options(server):
            setattr(self, option, Conf.get(server, option))

