#!/usr/bin/env python
'''
Install mail relay Client/Server


READ
http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch21_:_Configuring_Linux_Mail_Servers
http://www.phinesolutions.com/sendmail-gmail-smtp-relay-howto.html
http://www.eecis.udel.edu/~mills/mail/html/accopt.html

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import smtplib
from socket import gethostname

import app
import config
import general
from general import set_config_property, set_config_property2
from net import get_public_ip
import hardening
import iptables
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-mail-relay-server", install_mail_server, help="Install mail-relay server on the current server.")
  commands.add("install-mail-relay-client", install_mail_client, help="Install mail-relay client on the current server.")
  commands.add("uninstall-mail-relay", uninstall_mail, help="Uninstall mail-relay server on the current server.")

def install_mail_server(args):
  app.print_verbose("Install mail-relay-server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("Install-mail-relay-server", SCRIPT_VERSION)
  version_obj.check_executed()

  general.shell_exec("yum -y install sendmail")

  # Tell iptables that this server is configured as a mail-relay server.
  general.shell_exec("touch /etc/mail/syco_mail_relay_server")
  iptables.add_mail_relay_chain()
  iptables.save()

  hardening.network.configure_resolv_conf()
  hardening.network.configure_localhost()
  hardening.network.restart_network()

  app.print_verbose("Configure /etc/mail/*")

  # Allow all servers on localdomain to relay through this server.
  set_config_property2("/etc/mail/access", "Connect:10.100                          RELAY")
  x("/usr/sbin/makemap hash /etc/mail/access.db < /etc/mail/access")

  # Remove the loopback address restriction to accept email from the internet or intranet.
  set_config_property(
    "/etc/mail/sendmail.mc",
    r".*DAEMON_OPTIONS\(\`Port\=smtp\,Addr\=127\.0\.0\.1\, Name\=MTA\'\)dnl",
    r"dnl DAEMON_OPTIONS(`Port=smtp,Addr=127.0.0.1, Name=MTA')dnl")

  _rebuild_sendmail_config()

  _test_mail()
  version_obj.mark_executed()

def install_mail_client(args):
  app.print_verbose("Install mail-relay-server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("Install-mail-relay-client", SCRIPT_VERSION)
  version_obj.check_executed()

  general.shell_exec("yum -y install sendmail")

  file = "/etc/mail/sendmail.mc"
  domain = config.general.get_mail_relay_domain_name()

  app.print_verbose("Configure /etc/mail/*")

  # Set the mail-relay server.
  set_config_property(file,
    ".*define\(\`SMART_HOST\'\, \`.*\'\)dnl",
    "define(`SMART_HOST', `" + domain + "')dnl"
  )

  # FEATURE always_add_domain always masquerades email addresses, even if the
  # mail is sent from a user on the mail server to another user on the same
  # mail server.
  set_config_property2(file, "FEATURE(always_add_domain)dnl")

  # FEATURE masquerade_entire_domain makes sendmail masquerade servers named
  # *my-site.com, and *another-site.com as my-site.com. In other words, mail
  # from sales.my-site.com would be masqueraded as my-site.com. If this wasn't
  # selected, then only servers named my-site.com and my-othersite.com would be
  # masqueraded. Use this with caution when you are sure you have the necessary
  # authority to do this.
  set_config_property2(file, "FEATURE(masquerade_entire_domain)dnl")

  # FEATURE masquerade_envelope rewrites the email envelope just as
  # MASQUERADE_AS rewrote the header.
  set_config_property2(file, "FEATURE(masquerade_envelope)dnl")

  # FEATURE allmasquerade makes sendmail rewrite both recipient addresses and
  # sender addresses relative to the local machine. If you cc: yourself on an
  # outgoing mail, the other recipient sees a cc: to an address he knows instead
  # of one on localhost.localdomain.
  # TODO: need to be before MAILER
  #set_config_property2(file, "FEATURE(allmasquerade)dnl")

  # The MASQUERADE_AS directive makes all mail originating on
  # client appear to come from a server within the domain
  # DOMAIN by rewriting the email header.
  set_config_property(file, ".*MASQUERADE_AS\(\`.*\'\)dnl.*", "MASQUERADE_AS(`" + domain + "')dnl")

  # The MASQUERADE_DOMAIN directive makes mail relayed via mail-relay server
  # from all machines in the localdomain domains appear to come from the
  # MASQUERADE_AS domain. Using DNS, sendmail checks the domain name associated
  # with the IP address of the mail relay client sending the mail to help it
  # determine whether it should do masquerading or not.
  set_config_property2(file, "MASQUERADE_DOMAIN(localhost)dnl")
  set_config_property2(file, "MASQUERADE_DOMAIN(localhost.localdomain)dnl")

  # By default, user "root" will not be masqueraded. Removing the EXPOSED_USER
  # will also masqueraded root.
  set_config_property(file, ".*EXPOSED_USER\(\`root\'\)dnl.*", "dnl EXPOSED_USER(`root')dnl")

  _rebuild_sendmail_config()

  _test_mail()
  version_obj.mark_executed()

def uninstall_mail(args):
  '''
  Uninstall mail

  '''
  #iptables.del_mail_chain()
  #iptables.save()

  general.shell_exec("rm -rf /etc/mail")
  general.shell_exec("yum -y reinstall sendmail")

  version_obj = version.Version("Install-mail-relay", SCRIPT_VERSION)
  version_obj.mark_uninstalled()

def _rebuild_sendmail_config():
  general.shell_exec("yum -y install sendmail-cf")
  os.chdir("/etc/mail")
  general.shell_exec('make')
  general.shell_exec('service sendmail start')
  general.shell_exec("yum -y remove sendmail-cf")

def _test_mail():
  app.print_verbose("Send testmail for " + gethostname())

  email = config.general.get_admin_email()

  msg = ("From: %s\r\nTo: %s\r\nSubject: %s %s (%s)\r\n\r\n" % (
    email, email, "Mail relay client installed on ", gethostname(),
    get_public_ip()
  ))

  server = smtplib.SMTP('localhost')
  server.sendmail(email, email, msg)
  server.quit()
