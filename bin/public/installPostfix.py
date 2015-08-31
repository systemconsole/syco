#!/usr/bin/env python
'''
Install mail relay Client/Server

Postfix relay
http://wiki.centos.org/HowTos/postfix

Config according to
http://www.postfix.org/BASIC_CONFIGURATION_README.html

Postfix Client (unfortunately german, but only the commands are important)
http://www.werthmoeller.de/doc/microhowtos/postfix/postfix_smtp_auth/client/

'''

__author__ = "elis.kullberg@netlight.se"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lindh, Ronny Forberger"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Testing"


from general import set_config_property, set_config_property2, x
from net import get_public_ip, get_hostname
from augeas import Augeas
import app
import config
import general
import install
import net
import scopen
import version
import sys
from iptables import InboundFirewallRule, OutboundFirewallRule

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


class PostFixProperties():
    server_ips = []
    server_networks = []
    virtual_alias_domains = None
    virtual_aliases = {}

    def __init__(self):

        netmasks = {}

        #Add localhost IP/netmask
        local_ip = "127.0.0.1"
        self.server_ips.append(local_ip)
        netmasks[local_ip] = "255.0.0.0"

        #Add IPs for front/back net if they exist.
        front_ip = config.host(net.get_hostname()).get_front_ip()
        if front_ip:
            self.server_ips.append(front_ip)
            netmasks[front_ip] = config.general.get_front_netmask()
        back_ip = config.host(net.get_hostname()).get_back_ip()
        if config.general.is_back_enabled() and back_ip:
            self.server_ips.append(back_ip)
            netmasks[back_ip] = config.general.get_back_netmask()

        if len(self.server_ips) < 2:
            app.print_error("Didn't find any valid IP addresses from front or back net. Exiting")
            sys.exit(1)

        for ip in self.server_ips:
            self.server_networks.append(net.get_network_cidr(ip, netmasks[ip]))

        self.virtual_alias_domains = config.general.get_option("mailrelay.virtual_alias_domains", "")

        for alias_row in config.general.get_option("mailrelay.virtual_aliases", "").split(";"):
            if len(alias_row.strip()) == 0:
                #Don't process empty rows
                break
            split_row = alias_row.split(" ", 1)
            if len(split_row) != 2:
                app.print_error("Expected mailrelay.virtual_alias to be two words separated by space, several entries "
                                "separated by semicolon. Found \"%s\"" % alias_row)
                sys.exit(1)
            self.virtual_aliases[split_row[0]] = split_row[1]


def build_commands(commands):
    commands.add("install-postfix-server", install_mail_server,
                 help="Install postfix/mail-relay server on the current server.",
                 firewall_config=[InboundFirewallRule(service="postfix", ports=["25"])])
    commands.add("install-postfix-client", install_mail_client,
                 help="Install postfix/mail-relay client on the current server.",
                 firewall_config=[OutboundFirewallRule(service="postfix", ports=["25"],
                                                      dst=config.general.get_mailrelay_server_ip())])
    commands.add("uninstall-postfix-server", uninstall_mail_relay,
                 help="Uninstall postfix/mail-relay client on the current server.")
    commands.add("uninstall-postfix-client", uninstall_mail_relay,
                 help="Uninstall postfix/mail-relay client on the current server.")
    commands.add("send-test-email", send_test_mail, help="Send a test email to the sysop address")


def install_mail_server(args):
    """
    Installs a postfix-based mail relay MTA that listens on the DMZ, and relays
    towards the internet. Also possible to send from localhost. Also installs mailx.

    """
    version_obj = version.Version("Install-postfix-server", SCRIPT_VERSION)
    version_obj.check_executed()
    app.print_verbose("Installing postfix-server version: {0}".format(SCRIPT_VERSION))

    init_properties = PostFixProperties()

    # Install required packages
    x("yum install -y postfix augeas")

    #Initialize augeas
    augeas = Augeas(x)

    # Set config file parameters
    #
    general.use_original_file("/etc/postfix/main.cf")
    postfix_main_cf = scopen.scOpen("/etc/postfix/main.cf")

    # Hostname is full canonical name of machine.
    postfix_main_cf.replace("#myhostname = host.domain.tld", "myhostname = {0}".format(config.general.get_mail_relay_domain_name())) # mailrelay.syco.com
    postfix_main_cf.replace("#mydomain = domain.tld", "mydomain = {0}".format(config.general.get_resolv_domain())) # syco.com
    postfix_main_cf.replace("#myorigin = $mydomain", "myorigin = $myhostname")

    # Accept email from all IP addresses for this server
    augeas.set_enhanced("/files/etc/postfix/main.cf/inet_interfaces", ",".join(init_properties.server_ips))

    #Allow networks
    augeas.set_enhanced("/files/etc/postfix/main.cf/mynetworks", ",".join(init_properties.server_networks))

    # Do not relay anywhere special, i.e straight to internet.
    postfix_main_cf.replace("#relay_domains = $mydestination", "relay_domains =")
    postfix_main_cf.replace("#home_mailbox = Maildir/", "home_mailbox = Maildir/")

    # Stop warning about IPv6.
    postfix_main_cf.replace("inet_protocols = all", "inet_protocols = ipv4")

    #Set virtual_alias_maps and virtual_alias_domains in main.cf
    augeas.set("/files/etc/postfix/main.cf/virtual_alias_maps", "hash:/etc/postfix/virtual")

    if init_properties.virtual_alias_domains:
        augeas.set("/files/etc/postfix/main.cf/virtual_alias_domains", init_properties.virtual_alias_domains)

    #Add virtual aliases if they do not already exist
    for virt_alias_from, virt_alias_to in init_properties.virtual_aliases.iteritems():
        existing = augeas.find_entries("/files/etc/postfix/virtual/pattern[. = '%s']" % virt_alias_from)
        if len(existing) == 0:
            x("echo \"%s %s\" >> /etc/postfix/virtual" % (virt_alias_from, virt_alias_to))
        else:
            augeas.set_enhanced("/files/etc/postfix/virtual/pattern[. = '%s']/destination" % virt_alias_from,
                                virt_alias_to)

    if len(init_properties.virtual_aliases) > 0:
        x("postmap /etc/postfix/virtual")
    # Install a simple mail CLI-tool
    install_mailx()

    x("service postfix restart")

    # Send test mail to the syco admin
    # and to any virtual alias emails
    send_test_mail((None, config.general.get_admin_email()),
                   init_properties.virtual_aliases.keys())


def install_mail_client(args):
    """
    Installs a local postfix MTA which accepts email on localhost forwards
    relays everything to mailrelay-server. Also installs mailx.
    See line comments in install_mail_server

    """

    if config.host(net.get_hostname()).has_command_re("install-postfix-server"):
        app.print_verbose(
            "This server will later install the postfix server, abort client installation."
        )
        return

    version_obj = version.Version("Install-postfix-client", SCRIPT_VERSION)
    version_obj.check_executed()

    # Install required packages
    install.package("postfix")

    # Set config file parameters
    #
    general.use_original_file("/etc/postfix/main.cf")
    postfix_main_cf = scopen.scOpen("/etc/postfix/main.cf")
    postfix_main_cf.replace("#myhostname = host.domain.tld", "myhostname = {0}.{1}".format(get_hostname(), config.general.get_resolv_domain())) # monitor.syco.com
    postfix_main_cf.replace("#mydomain = domain.tld", "mydomain = {0}".format(config.general.get_resolv_domain())) # syco.com
    postfix_main_cf.replace("#myorigin = $mydomain", "myorigin = $myhostname")

    # Listen only on localhost
    postfix_main_cf.replace("inet_interfaces = localhost", "inet_interfaces = localhost")
    postfix_main_cf.replace("#mynetworks = 168.100.189.0/28, 127.0.0.0/8", "mynetworks = 127.0.0.1")
    postfix_main_cf.replace("mydestination = $myhostname, localhost.$mydomain, localhost", "mydestination = $myhostname, localhost")

    # Relay everything not for local machine to mailrelay.
    postfix_main_cf.replace("#relay_domains = $mydestination", "relay_domains = {0}".format(config.general.get_resolv_domain()))
    postfix_main_cf.replace("#relayhost = $mydomain","relayhost = [{0}]".format(config.general.get_mail_relay_domain_name()))
    postfix_main_cf.replace("#home_mailbox = Maildir/","home_mailbox = Maildir/")
    postfix_main_cf.replace("inet_protocols = all","inet_protocols = ipv4")

    # Install a simple mail CLI-tool
    install_mailx()

    # Tell iptables and nrpe that this server is configured as a mail-relay server.
    iptables.add_mail_relay_chain()
    iptables.save()

    # Restart postfix
    x("service postfix restart")

    # Send test mail to the syco admin
    send_test_mail((None, config.general.get_admin_email()))


def install_mailx():
    """
    Installs mailx for classic "mail -s "subject" destemail" from terminal.

    """
    x("yum install -y mailx")


def uninstall_mail_relay(args):
    """
    Uninstalls postfix and mailx.

    """
    app.print_verbose("Removing mail-relay chain")

    # Remove package and rpmsave of cfg
    x("yum remove postfix mailx -y")
    x("rm -rf /etc/postfix")

    # Remote iptables chains
    iptables.del_mail_relay_chain()
    iptables.save()


def send_test_mail(args, additional_emails_to_test=[]):
    """
    Sends a test-email either to admin email or argv email if present using mailx.

    """
    app.print_verbose("Send testmail for " + get_hostname())

    try:
        email = args[1]
    except IndexError:
        email = config.general.get_admin_email()

    x('echo "" | mail -s "Test email from {0}. Installation complete!" {1}'.format(get_hostname(), email))

    for email in additional_emails_to_test:
        app.print_verbose("Send additional test mail to: %s" % email)
        x('echo "" | mail -s "Test email to {0}" {0}.'.format(email))

