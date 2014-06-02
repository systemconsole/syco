#!/usr/bin/env python
'''
Installs the main firewall

Input arguments:
    A configuration file. Example located in
        syco-private/var/firewall/fo-fw-example.cfg

Expected behavior (and recomended command order):

    install-firewall-interfaces: Bonds 2 or 4 interfaces in mode 1, and attatches
        bridges with correct IP-config.

    install-firewall-aliases:    Creates an alias (i.e ifcfg-br1:n file) in the
        network-scripts folder for every public IP in the config file.

    install-firewall-iptables:   Set up a firewall by modifying nat/filter
        table in the kernel. See code comments. All existing iptables
        rules will be flushed!

Recomended reading
    "man iptables"
    http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch14_:_Linux_Firewalls_Using_iptables
    http://wiki.centos.org/HowTos/Network/IPTables


'''

__author__ = "elis.kullberg@netlight.com"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "tbd"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lindh, Mattias Hemingsson"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Test"

import ConfigParser
import iptables as syco_iptables
from scopen import scOpen

from general import x
import app
import config
import general
import install
import net
import os
import version
import netUtils

iptables = "/sbin/iptables"

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1



def build_commands(commands):
  commands.add("install-firewall-interfaces", install_interfaces, "[config-file]", help="Bonds main firewall interfaces sets up bridges ready for more public aliases")
  commands.add("install-firewall-aliases",    install_aliases,    "[config-file]", help="Installs aliases for public IPs")
  commands.add("install-main-firewall",       install_iptables,   "[config-file]", help="Install iptables-based main firewall")


def install_interfaces(args):
    """
    Bonds 2 or 4 interfaces in mode 1, and attatches bridges with correct network-config.
    """
    version_obj = version.Version("InstallInterfaces", SCRIPT_VERSION)
    version_obj.check_executed()

    app.print_verbose("Setting up firewall interfaces")
    (c, conf) = _parse_config_file(args[1])
    print c
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


def install_iptables(args):
  """
  Installs an iptables-based rule set. Then flushes currenly loaded iptables.
  Then applies general input/output/forwarding filter rules, then applies
  specific filter/DNAT rules on a per-host basis according to the config file.
  Finally adds SNAT for all traffic to external IPs. Finally saves the config,
  i.e makes it statful.

  """
  app.print_verbose("Installing firewall")
  version_obj = version.Version("InstallFirewall", SCRIPT_VERSION)
  version_obj.check_executed()

  (c, conf) = _parse_config_file(args[1])
  load_modules()
  flush_tables()

  # Setup global & input/output chain filtering
  setup_global_filters()
  setup_io_filters(c)
  setup_temp_io_filters(c)

  # Setup DNAT/SNAT & forward chain filtering
  setup_forwarding(c,conf)
  setup_source_nat(c)

  # Close global filters log packets that fell through
  close_global_filters()

  # Make changes stateful
  save_settings()
  app.print_verbose("Done - safe surfing!")

  version_obj.mark_executed


def allow_clients_to_access_external_dns(c):
    """
    Could potentially be inactivated once dns-server is installed and running
    """
    dns_list = c.dns.primary_dns.replace(" ","").split(',')
    for dns in dns_list:
        forward_tcp(source_interface=c.interfaces.dmz_interface, dest_ip=dns,
            source_ports="53,1024:65535", dest_ports="53", state="NEW", next_chain="allowed_tcp")
        forward_udp(source_interface=c.interfaces.dmz_interface, dest_ip=dns,
            source_ports="53,1024:65535", dest_ports="53", state="NEW", next_chain="allowed_udp")

def allow_firewall_to_access_external_dns(c):
    """
    Could potentially be inactivated once dns-server is installed and running
    """
    dns_list = c.dns.primary_dns.replace(" ","").split(',')
    for dns in dns_list:
        allow_tcp_out(dest_interface=c.interfaces.internet_interface, dest_ip=dns,
            source_ports="1024:65535", dest_ports="53", state="NEW", next_chain="allowed_tcp")
        allow_udp_out(dest_interface=c.interfaces.internet_interface, dest_ip=dns,
            source_ports="1024:65535", dest_ports="53", state="NEW", next_chain="allowed_udp")


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
    Load relevant kernel modules (not implemented since this works
    automagically in centos 6.3)

    """
    app.print_verbose("Load modules")
    x("modprobe nf_conntrack") # Probably not needed
    x("modprobe nf_conntrack_ftp ports=21") # Needed
    x("modprobe nf_nat_ftp ports=21") # Needed


def _parse_config_file(filepath):
    """
    This method parses the separate configuration file.

    Return value: An ConfigBranch-object containing a tree-structure of all
                  configuration for easy access.

    """
    app.print_verbose("Parsing configuration file")
    Conf = ConfigParser.ConfigParser()
    Conf.read(filepath)
    c = ConfigBranch(Conf)
    return (c, Conf)

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
    snat_all(source_ip = c.interfaces.dmz_ip+c.interfaces.dmz_netmask, dest_interface=c.interfaces.dmz_interface, snat_ip=c.interfaces.dmz_ip)



def close_global_filters():
    # Log all packages reching this. We shouldn't get them.
    x(iptables + ' -A INPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "IPT INPUT packet died: "')
    x(iptables + ' -A OUTPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "IPT OUTPUT packet died: "')
    x(iptables + ' -A FORWARD -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "IPT FORWARD packet died: "')

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

    # Makes kernel settings stateful
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

    allow_clients_to_access_external_dns(c)

    setup_specific_forwarding(c, conf)

    # DMZ are allowed to access DMZ
    forward_all(source_interface=c.interfaces.dmz_interface, dest_interface=c.interfaces.dmz_interface)

    # The IP below belongs to Netgiro, used by FP
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="195.149.170.66")

    # Everybody are allowd to access Enterprise servers
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="vanguardcar.com")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="www.vanguardcar.com")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="uat.vanguardcar.com")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="mo.vanguardcar.com")

    # Everybody are allowd to whois servers
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="whois.nic-se.se", dest_ports="43")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="whois.ripe.net", dest_ports="43")

    # Everybody is allowed to use Ubuntu key-servers
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="keyserver.ubuntu.com", dest_ports="11371")

    # Everybody is allowed to SSH out
    #forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ports="22,34,8022")

    # Everybody is allowed to access HTTP HTTPS
    # TODO -  allow the repo-list URL's and nothing else DONT USE THIS RULE
    #forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ports="80,443") # yum

    # Open rsync to internet
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ftp.sunet.se", dest_ports="873")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ftp.df.lth.se", dest_ports="873")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="mirrors.se.eu.kernel.org", dest_ports="873")

    #Clamav update servers
    #New version download
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="sourceforge.net", dest_ports="80")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="downloads.sourceforge.net", dest_ports="80")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="heanet.dl.sourceforge.net", dest_ports="80")
    #Virus def updates
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="db.se.clamav.net", dest_ports="80")
    
    #Yum update servers
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="mirrorlist.centos.org", dest_ports="80")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="mirror.nsc.liu.se", dest_ports="80")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ftp.sunet.se", dest_ports="80")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ftp.sunet.se", dest_ports="21")

    #Openvas Rules
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="feed.openvas.org", dest_ports="873")

    #Fareoffice VSC
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="vcs.fareoffice.com", dest_ports="443")		

    #Download packages from Fareoffice package server
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="packages.fareoffice.com", dest_ports="80")

    #Github - List maintained at:
    #https://help.github.com/articles/what-ip-addresses-does-github-use-that-i-should-whitelist
    #Added whole IP ranges as github uses a defunct random DNS response within these ranges...
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="207.97.227.224/27", dest_ports="22,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="173.203.140.192/27", dest_ports="22,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="204.232.175.64/27", dest_ports="22,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="72.4.117.96/27", dest_ports="22,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="192.30.252.0/22", dest_ports="22,443")
    #Github CDN
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="raw.github.com", dest_ports="443")

    #Scala/play repo servers
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="repo.typesafe.com", dest_ports="80")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="scalasbt.artifactoryonline.com", dest_ports="80")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="repo1.maven.org", dest_ports="80")

    #RentalFront
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="www.fareoffice.com", dest_ports="21")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="maps.google.com", dest_ports="80,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="www.google.com", dest_ports="80,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ws.enterprise.com", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="webserv.enterprise.com", dest_ports="443")
       
    # Hertz / Excalibur
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="vv.xnet.hertz.com", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="12.5.245.37", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="12.147.231.37", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="12.28.81.37", dest_ports="443")    
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="vv.xqual.hertz.com", dest_ports="443")

    # Europcar
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="eservice-tst.rentpremier.com", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="eservice-rls.rentpremier.com", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="eservice-bck.rentpremier.com", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="eservice-ptn.rentpremier.com", dest_ports="443")
    
    # WebRes
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="www.vanguardcar.com", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="mo.vanguardcar.com", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="uat.vanguardcar.com", dest_ports="443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ftp.alamo.com", dest_ports="21")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ftp.enterprise.com", dest_ports="21")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="hertz.worktribe.com", dest_ports="80,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="www.webservicex.net", dest_ports="80,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ftp.newsletter.nationalcar.co.uk", dest_ports="22")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="ftp.newsletter.alamo.co.uk", dest_ports="22")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="v1.alamo.com", dest_ports="80")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="www.nationalcar.com", dest_ports="80")


    #Allow to AV Location
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="88.80.170.134", dest_ports="80,443")
    forward_tcp(dest_interface=c.interfaces.internet_interface, dest_ip="88.80.170.132", dest_ports="80,443")

    setup_specific_forwarding(c, conf)

def setup_specific_forwarding(c, Conf):
    """
    Parse through config file and set up forwarding for all hosts that should
    be accessible on a public IP, or need access to external services on a
    specifig port. Options for access type are port and protocol. Also handles
    DNAT.

    """
    app.print_verbose("Setting up forwarding chain")

    for server in Conf.sections():
        for option in Conf.options(server):
            # Nice one liner - try: globals()[option]("parameters") - basically function pointers in python
            # To do - proper handling of function arguments using my data-structure
            if option == "allow_tcp_in":
                forward_tcp(dest_interface=c.interfaces.dmz_interface, dest_ip=Conf.get(server, "dmz_ip"), dest_ports=Conf.get(server,option))
                dnat_tcp(dest_ip=Conf.get(server,"internet_ip"), dest_ports=Conf.get(server, option), dnat_ip=Conf.get(server,"dmz_ip"))
            elif option == "allow_udp_in":
                forward_udp(dest_interface=c.interfaces.dmz_interface, dest_ip=Conf.get(server, "dmz_ip"), dest_ports=Conf.get(server,option))
                dnat_udp(dest_ip=Conf.get(server,"internet_ip"), dest_ports=Conf.get(server, option), dnat_ip=Conf.get(server,"dmz_ip"))
            elif option == "allow_icmp_in":
                forward_icmp(dest_interface=c.interfaces.dmz_interface, dest_ip=Conf.get(server, "dmz_ip"))
            elif option == "allow_tcp_out":
                forward_tcp(source_interface=c.interfaces.dmz_interface, source_ip=Conf.get(server, "dmz_ip"), dest_ports=Conf.get(server, option))
                # If host has a internet_ip it should leave the firewall on that
                # ip or else use the default public ip for the fw, which is
                # defined in postrouting().
                if Conf.has_option(server, "internet_ip"):
                    internet_ip = Conf.get(server, "internet_ip")
                    snat_tcp(
                        #source_interface=c.interfaces.dmz_interface,
                        source_ip=Conf.get(server, "dmz_ip"),
                        dest_interface=c.interfaces.internet_interface,
                        dest_ports=Conf.get(server, option),
                        snat_ip=internet_ip
                    )

            elif option == "allow_udp_out":
                forward_udp(source_interface=c.interfaces.dmz_interface, source_ip=Conf.get(server, "dmz_ip"), dest_ports=Conf.get(server,option))
                # If host has a internet_ip it should leave the firewall on that
                # ip or else use the default public ip for the fw, which is
                # defined in postrouting().
                if Conf.has_option(server, "internet_ip"):
                    internet_ip = Conf.get(server, "internet_ip")
                    snat_udp(
                        #source_interface=c.interfaces.dmz_interface,
                        source_ip=Conf.get(server, "dmz_ip"),
                        dest_interface=c.interfaces.internet_interface,
                        dest_ports=Conf.get(server, option),
                        snat_ip=internet_ip
                    )

            elif option == "allow_icmp_out":
                forward_icmp(source_interface=c.interfaces.dmz_interface, source_ip=Conf.get(server, "dmz_ip"))


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
    inet_interface_network = str(inet_network.network)
    inet_interface_netmask = str(inet_network.netmask)

    for section in conf.sections():
        if (conf.has_option(section, "internet_ip")) and (section != "interfaces"):
            # Text in alias-file
            aliastext = """
DEVICE=%s
IPADDR=%s
TYPE=Ethernet
BOOTPROTO=none
BROADCAST=%s
NETMASK=%s
ONBOOT=yes""" %  (inet_interface + ":" + (conf.get(section, "internet_ip")).split(".")[3], conf.get(section, "internet_ip"), inet_interface_broadcast, inet_interface_netmask)

            # Filename for alias file
            aliasfilename = "/etc/sysconfig/network-scripts/ifcfg-" + inet_interface + ":" + (conf.get(section, "internet_ip")).split(".")[3]
            general.store_file(aliasfilename, aliastext)

    x("service network restart")


def delete_aliases(conf):
    """
    Delete all ifcfg files created by this script before.

    """
    inet_interface = conf.get("interfaces", "internet_interface")
    app.print_verbose("Remove aliases for device {0}".format(inet_interface))

    path = "/etc/sysconfig/network-scripts/"
    dirList=os.listdir(path)
    for fname in sorted(dirList):
        if fname.startswith('ifcfg-{0}:'.format(inet_interface)):
            full_path = path + fname
            x('ifdown %s' % fname)
            os.unlink(full_path)


def setup_interfaces(c):
    """
    Bonds ethernet-interfaces in mode 1, and adds bonds to a bridge. Supports
    both 2 and 4 NIC machines (even though bonds arent very useful in the
    former type!). Kernel bond aliases are stateful.

    """
    app.print_verbose("Setting up firewall interfaces.")
    install.package("python-ipaddr")
    import ipaddr

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

    inet_network = ipaddr.IPv4Network(c.interfaces.internet_ip
        + c.interfaces.internet_netmask)
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

    if (num_of_if >= 4):
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
    elif (num_of_if == 2):
        # Setup back-net
        netUtils.setup_bridge("br0", back_ip, back_netmask, back_gw, back_resolver)
        netUtils.setup_bond("bond0", "br0")
        netUtils.setup_eth("eth0", "bond0")

        # _setup front-net
        netUtils.setup_bridge("br1", front_ip, front_netmask, front_gw, front_resolver)
        netUtils.setup_bond("bond1", "br1")
        netUtils.setup_eth("eth1", "bond1")
    else:
        raise Exception("To few network interfaces: " + str(num_of_if))

    x("service network restart")


def setup_io_filters(c):
    """
    Rules that affect the firewall's INPUT/OUTPUT chains. I.e they affect
    communication with a firewall IP as origin/destination.  Rules are shared
    with the syco-iptables script active in all other machines. However,
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
    syco_iptables.setup_dns_resolver_rules()



def setup_temp_io_filters(c):
    '''
    Optimally, firewall should not be able to be accessed/access anything via
    input/output chains on the  internet interface. However, a few exceptions
    are needed initially.

    '''
    # Temporary rules to allow SSH in/out
    # Only ssh from bounce server at a later date
    #allow_tcp_in(dest_ports="22,8022",dest_ip=c.interfaces.internet_ip)
    allow_tcp_in(dest_ports="22,8022",dest_ip=c.interfaces.dmz_ip)
    #allow_tcp_out(dest_ports="22,8022",
    #    dest_interface=c.interfaces.internet_interface)
    allow_tcp_out(dest_ports="22,8022",
        dest_interface=c.interfaces.dmz_interface)

    # Temporary rules to allow port 80 out
    # Only access to internal install server at a later date
    #allow_tcp_out(dest_ports="80,443",
    #    dest_interface=c.interfaces.internet_interface)

    # Temporary tile to allow DNS access
    # Only access to external dns at a later date
    #allow_firewall_to_access_external_dns(c)


#
# Helper functions and classes
#


### FILTER TABLE, INPUT CHAIN ####


def allow_all_in(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain = False):
    allow_tcp_in(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="allowed_tcp")
    allow_udp_in(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="allowed_udp")
    allow_icmp_in(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="icmp_packets")


def allow_tcp_in(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_tcp"):
    allow_command = _build_iptable_command(table, source_ip, dest_ip, "INPUT", "tcp", source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(allow_command)


def allow_udp_in(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_udp"):
    allow_command = _build_iptable_command(table, source_ip, dest_ip, "INPUT", "udp", source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(allow_command)


def allow_icmp_in(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="icmp_packets"):
    allow_command = _build_iptable_command(table, source_ip, dest_ip, "INPUT", "ICMP", source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(allow_command)

### FILTER TABLE, OUTPUT CHAIN ###


def allow_all_out(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain=False):
    allow_tcp_out(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="allowed_tcp")
    allow_udp_out(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="allowed_udp")
    allow_icmp_out(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="icmp_packets")


def allow_tcp_out(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_tcp"):
    allow_command = _build_iptable_command(table, source_ip, dest_ip, "OUTPUT", "tcp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(allow_command)


def allow_udp_out(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_udp"):
    allow_command = _build_iptable_command(table, source_ip, dest_ip, "OUTPUT", "udp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(allow_command)


def allow_icmp_out(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="icmp_packets"):
    allow_command = _build_iptable_command(table, source_ip, dest_ip, "OUTPUT", "ICMP",source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(allow_command)


### FILTER TABLE, FORWARDING CHAIN ####


def forward_all(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain=False):
    forward_tcp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="allowed_tcp")
    forward_udp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="allowed_udp")
    forward_icmp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain="icmp_packets")


def forward_tcp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_tcp"):
    forward_command = _build_iptable_command(table, source_ip, dest_ip, "FORWARD", "tcp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(forward_command)


def forward_udp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state="NEW", next_chain="allowed_udp"):
    forward_command = _build_iptable_command(table, source_ip, dest_ip, "FORWARD", "udp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(forward_command)


def forward_icmp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="icmp_packets"):
    forward_command = _build_iptable_command(table, source_ip, dest_ip, "FORWARD", "ICMP",source_interface, source_ports, dest_ports, dest_interface, state, next_chain)
    x(forward_command)


### NAT TABLE, PREROUTING CHAIN ###


def dnat_all(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="DNAT", dnat_ip=False):
    dnat_tcp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)
    dnat_udp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)
    dnat_icmp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)


def dnat_tcp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="DNAT", dnat_ip=False):
    dnat_command = _build_iptable_command("nat", source_ip, dest_ip, "PREROUTING", "tcp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)
    x(dnat_command)


def dnat_udp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="DNAT", dnat_ip=False):
    dnat_command = _build_iptable_command("nat", source_ip, dest_ip, "PREROUTING", "udp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)
    x(dnat_command)


def dnat_icmp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="DNAT", dnat_ip=False):
    dnat_command = _build_iptable_command("nat", source_ip, dest_ip, "PREROUTING", "icmp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip)
    x(dnat_command)


### NAT TABLE, POSTROUTING CHAIN ###


def snat_all(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="SNAT", dnat_ip=False, snat_ip=False):
    snat_tcp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip, snat_ip)
    snat_udp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip, snat_ip)
    snat_icmp(table, source_ip, dest_ip, source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip, snat_ip)


def snat_tcp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="SNAT", dnat_ip=False, snat_ip=False):
    snat_command = _build_iptable_command("nat", source_ip, dest_ip, "POSTROUTING", "tcp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip,snat_ip)
    x(snat_command)


def snat_udp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="SNAT", dnat_ip=False, snat_ip=False):
    snat_command = _build_iptable_command("nat", source_ip, dest_ip, "POSTROUTING", "udp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip ,snat_ip)
    x(snat_command)


def snat_icmp(table=False, source_ip=False, dest_ip=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="SNAT", dnat_ip=False, snat_ip=False):
    snat_command = _build_iptable_command("nat", source_ip, dest_ip, "POSTROUTING", "icmp",source_interface, source_ports, dest_ports, dest_interface, state, next_chain, dnat_ip ,snat_ip)
    x(snat_command)


def _build_iptable_command(table=False, source_ip=False, dest_ip=False, chain=False, protocol=False, source_interface=False, source_ports=False, dest_ports=False, dest_interface=False, state=False, next_chain="ACCEPT", dnat_ip=False, snat_ip=False):
    '''
    Build the command element by element (might be able to use ":" as wildcard
    for d/sport, and "[+]" for interface wildcard to save some lines

    '''
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
    command = iptables + string_table + string_chain + string_protocol + string_source_ip + string_source_interface + string_source_ports + string_dest_ip + string_dest_ports + string_dest_interface + string_state + string_next_chain + string_dnat_ip + string_snat_ip
    return command


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

