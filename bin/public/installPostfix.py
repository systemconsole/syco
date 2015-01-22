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

import os
import smtplib


from general import set_config_property, set_config_property2, x
from net import get_public_ip, get_hostname
import app
import config
import general
import hardening
import install
import iptables
import net
import scopen
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

class PostFixProperties():
    server_front_ip = None
    server_back_ip = None
    server_network_front = None
    server_network_back = None

    def __init__(self):
        server_front_ip = config.host(net.get_hostname()).get_front_ip()
        server_back_ip = config.host(net.get_hostname()).get_back_ip()

        server_network_front = net.get_network_cidr(server_front_ip,
            config.general.get_front_netmask())

        server_network_back = net.get_network_cidr(server_back_ip,
            config.general.get_back_netmask())

def build_commands(commands):
  commands.add("install-postfix-server", install_mail_server, help="Install postfix/mail-relay server on the current server.")
  commands.add("install-postfix-client", install_mail_client, help="Install postfix/mail-relay client on the current server.")
  commands.add("uninstall-postfix-server", uninstall_mail_relay, help="Uninstall postfix/mail-relay client on the current server.")
  commands.add("uninstall-postfix-client", uninstall_mail_relay, help="Uninstall postfix/mail-relay client on the current server.")
  commands.add("send-test-email", send_test_mail, help="Send a test email to the sysop address")


def install_mail_server(args):
  '''
  Installs a postfix-based mail relay MTA that listens on the DMZ, and relays
  towards the internet. Also possible to send from localhost. Also installs mailx.

  '''
  version_obj = version.Version("Install-postfix-server", SCRIPT_VERSION)
  version_obj.check_executed()
  app.print_verbose("Installing postfix-server version: {0}".format(SCRIPT_VERSION))

  init_properties = PostFixProperties()

  # Install required packages
  install.package("postfix")

  # Set config file parameters
  #
  general.use_original_file("/etc/postfix/main.cf")
  postfix_main_cf = scopen.scOpen("/etc/postfix/main.cf")

  # Hostname is full canonical name of machine.
  postfix_main_cf.replace("#myhostname = host.domain.tld", "myhostname = {0}".format(config.general.get_mail_relay_domain_name())) # mailrelay.syco.com
  postfix_main_cf.replace("#mydomain = domain.tld", "mydomain = {0}".format(config.general.get_resolv_domain())) # syco.com
  postfix_main_cf.replace("#myorigin = $mydomain", "myorigin = $myhostname")

  # Accept email from frontnet and backnet
  postfix_main_cf.replace("inet_interfaces = localhost", "inet_interfaces = 127.0.0.1,{0},{1}".format(init_properties.server_front_ip,init_properties.server_back_ip))
  postfix_main_cf.replace("#mynetworks = 168.100.189.0/28, 127.0.0.0/8", "mynetworks = {0}, {1}, 127.0.0.0/8".format(init_properties.server_network_front,init_properties.server_network_back))

  # Do not relay anywhere special, i.e straight to internet.
  postfix_main_cf.replace("#relay_domains = $mydestination", "relay_domains =")
  postfix_main_cf.replace("#home_mailbox = Maildir/", "home_mailbox = Maildir/")

  # Stop warning about IPv6.
  postfix_main_cf.replace("inet_protocols = all", "inet_protocols = ipv4")

  # Install a simple mail CLI-tool
  install_mailx()

  # Tell iptables and nrpe that this server is configured as a mail-relay server.
  iptables.add_mail_relay_chain()
  iptables.save()

  x("service postfix restart")

  # Send test mail to the syco admin
  send_test_mail((None, config.general.get_admin_email()))


def install_mail_client(args):
  '''
  Installs a local postfix MTA which accepts email on localhost forwards
  relays everything to mailrelay-server. Also installs mailx.
  See line comments in install_mail_server

  '''

  init_properties()

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
  '''
  Installs mailx for classic "mail -s "subject" destemail" from terminal.

  '''
  install.package("mailx")


def uninstall_mail_relay():
  '''
  Uninstalls postfix and mailx.

  '''
  init_properties()
  app.print_verbose("Removing mail-relay chain")

  # Remove package and rpmsave of cfg
  x("yum remove postfix mailx -y")
  x("rm -rf /etc/postfix")

  # Remote iptables chains
  iptables.del_mail_relay_chain()
  iptables.save()


def send_test_mail(args):
  '''
  Sends a test-email either to admin email or argv email if present using mailx.

  '''
  app.print_verbose("Send testmail for " + get_hostname())

  try:
    email = args[1]
  except IndexError:
    email = config.general.get_admin_email()

  x('echo "" | mail -s "Test email from {0}" {1}'.format(get_hostname(), email))
