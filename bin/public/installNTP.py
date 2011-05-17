#!/usr/bin/env python
'''
Install NTP Client/Server

http://www.cyberciti.biz/faq/rhel-fedora-centos-configure-ntp-client-server/
http://www.pool.ntp.org/en/use.html
http://www.gsp.com/cgi-bin/man.cgi?section=5&topic=ntp.conf

Shell commands that can be nice to use when testing.
ntpdate -qdv localhost
ntpq -pn
ntptrace
watch ntpq -c lpee

TODO
* Anything speial that needs to be done on KVM guests?
* SSL or other keys to the ntp server?

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
import app, general, version, iptables

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-ntp", install_ntp, "[ntp-server-ip]", help="Install ntp server on the current server. Optional ntp-server-ip")
  commands.add("uninstall-ntp", uninstall_ntp, help="Uninstall ntp server on the current server.")

def install_ntp(args):
  '''
  Install and configure the ntp-server on the local host.

  '''
  app.print_verbose("Install NTP version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallNTP", SCRIPT_VERSION)
  version_obj.check_executed()

  # Get ntp-server-ip from command line.
  ntp_server_ip=False
  if (len(args)==2):
    ntp_server_ip=str(args[1])
    app.print_verbose("Using customized ntp-server-ip: " + ntp_server_ip)

  # Install the NTP packages.
  if (not os.access("/etc/ntp.conf", os.F_OK)):
    general.shell_exec("yum -y install ntp")

  general.shell_exec("chkconfig ntpd on")

  iptables.add_ntp_chain()
  iptables.save()

  # Set ntp-server configs
  #
  # For restrict info: http://www.eecis.udel.edu/~mills/ntp/html/accopt.html
  #
  if (ntp_server_ip):
    app.print_verbose("Configure /etc/ntp.conf as a client")

    # Deny packets of all kinds, including ntpq(8) and ntpdc(8) queries.
    general.set_config_property("/etc/ntp.conf", "restrict default.*", "restrict default ignore")
    general.set_config_property("/etc/ntp.conf", "restrict -6 default.*", "restrict -6 default ignore")

    # Using only internal NTP-server.
    general.set_config_property("/etc/ntp.conf", "server 0.*ntp.org", "server " + ntp_server_ip + " burst")
    general.set_config_property("/etc/ntp.conf", ".*server 1.*ntp.org", "#server 1.se.pool.ntp.org")
    general.set_config_property("/etc/ntp.conf", ".*server 2.*ntp.org", "#server 2.se.pool.ntp.org")

    # Allow access to/from the ntp-server. You may use either a hostname or IP address
    # on the server line. You must use an IP address on the restrict line. Or do I??
    general.set_config_property("/etc/ntp.conf", "restrict " + ntp_server_ip + " kod nomodify notrap nopeer noquery", "restrict " + ntp_server_ip + " kod nomodify notrap nopeer noquery")
    general.set_config_property("/etc/ntp.conf", "restrict -6 " + ntp_server_ip + " kod nomodify notrap nopeer noquery", "restrict -6 " + ntp_server_ip + " kod nomodify notrap nopeer noquery")

    # Don't use fudge server
    general.set_config_property("/etc/ntp.conf", ".*server.*127.127.1.0.*", "#server 127.127.1.0")
    general.set_config_property("/etc/ntp.conf", ".*fudge.*127.127.1.0.*", "#fudge  127.127.1.0 stratum 10")

    # This command modifies the ntpd panic threshold (which is normally 1024
    # seconds). Setting this to 0 disables the panic sanity check and a clock
    # offset of any value will be accepted.
    general.set_config_property("/etc/ntp.conf", ".*tinker panic.*", "tinker panic 0")
  else:
    app.print_verbose("Configure /etc/ntp.conf as a server")
    general.set_config_property("/etc/ntp.conf", "server 0.*ntp.org", "server 0.se.pool.ntp.org")
    general.set_config_property("/etc/ntp.conf", "server 1.*ntp.org", "server 1.se.pool.ntp.org")
    general.set_config_property("/etc/ntp.conf", "server 2.*ntp.org", "server 2.se.pool.ntp.org")

  general.shell_exec("service ntpd start")

  version_obj.mark_executed()

def uninstall_ntp(args):
  '''
  Uninstall NTP

  '''
  if (os.access("/etc/ntp.conf", os.F_OK)):
    general.shell_exec("service ntpd stop")
  general.shell_exec("yum -y remove ntp ")

  iptables.del_ntp_chain()
  iptables.save()

  version_obj = version.Version("InstallNTP", SCRIPT_VERSION)
  version_obj.mark_uninstalled()
