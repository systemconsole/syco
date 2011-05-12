#!/usr/bin/env python
'''
Install cobbler.

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
import shutil
import time
import subprocess

import app
import general
import iptables
import version
import install

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-cobbler", install_cobbler, help="Install cobbler on the current server.")
  commands.add("install-cobbler-config", setup_all_systems, help="Refresh install.cfg settings to cobbler.")
  commands.add("refresh-cobbler-repo", refresh_repo, help="Refresh all repos on the cobbler server.")

def install_cobbler(args):
  '''
  Install cobbler on current host

  '''
  app.print_verbose("Install cobbler version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("installCobbler", SCRIPT_VERSION)
  version_obj.check_executed()

  _setup_firewall()
  _install_cobbler()
  _modify_coppler_settings()
  _import_repos()
  _refresh_all_profiles()
  setup_all_systems(args)
  _cobbler_sync
  version_obj.mark_executed()

def setup_all_systems(args):
  '''
  Update cobbler with all settings in install.cfg.

  '''
  _refresh_all_profiles()
  _remove_all_systems()
  for host_name in app.get_servers():
    ip = app.get_ip(host_name)

    # IS KVM host?
    if (len(app.get_guests(host_name))):
      app.print_verbose("Install host " + host_name + "(" + ip + ")")
      _host_add(host_name, ip)
    else:
      app.print_verbose("Install guest " + host_name + "(" + ip + ")")
      _guest_add(host_name, ip)

  _cobbler_sync()

def refresh_repo(args):
  '''
  Refresh all repos on the cobbler/repo server.

  Syco uses lots of external files, this function downloads all latest
  versions.

  TODO: Move the downloads array to each script, and this function
  should retrieve a download array from each script.

  '''
  downloads = {}
  downloads['jdk-6u24-linux-x64-rpm.bin'] = 'http://cds.sun.com/is-bin/INTERSHOP.enfinity/WFS/CDS-CDS_Developer-Site/en_US/-/USD/VerifyItem-Start/jdk-6u24-linux-x64-rpm.bin?BundledLineItemUUID=pGSJ_hCvabIAAAEu870pGPfd&OrderID=1ESJ_hCvsh4AAAEu1L0pGPfd&ProductID=oSKJ_hCwOlYAAAEtBcoADqmS&FileName=/jdk-6u24-linux-x64-rpm.bin'

  for dst, src in downloads.items():
    general.shell_exec("wget --background -O /var/www/cobbler/repo_mirror/" + dst + " "  + src)

  while(True):
    num_of_processes = subprocess.Popen("ps aux | grep wget", stdout=subprocess.PIPE, shell=True).communicate()[0].count("\n")
    if num_of_processes <=2:
      break
    app.print_verbose(str(num_of_processes-2) + " processes running, wait 10 more sec.")
    time.sleep(10)

  general.shell_exec("cobbler reposync")
  general.shell_exec("cobbler sync")

def _setup_firewall():
  '''
  Setup iptables rules

  TODO: Move to iptables.py ??

  '''

  # Create input chain
  iptables.iptables("-D INPUT -j Fareoffice-Input")
  iptables.iptables("-F Fareoffice-Input")
  iptables.iptables("-X Fareoffice-Input")
  iptables.iptables("-N Fareoffice-Input")
  iptables.iptables("-I INPUT 1 -j Fareoffice-Input")

  # TFTP - TCP/UDP
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m tcp -p tcp --dport 69 -j ACCEPT")
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m udp -p udp --dport 69 -j ACCEPT")

  # NTP
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m udp -p udp --dport 123 -j ACCEPT")

  # DHCP
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m udp -p udp --dport 67 -j ACCEPT")
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m udp -p udp --dport 68 -j ACCEPT")

  # HTTP/HTTPS
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT")
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m tcp -p tcp --dport 443 -j ACCEPT")

  # Syslog for cobbler
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m udp -p udp --dport 25150 -j ACCEPT")

  # Koan XMLRPC ports
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m tcp -p tcp --dport 25151 -j ACCEPT")
  iptables.iptables("-A Fareoffice-Input -m state --state NEW -m tcp -p tcp --dport 25152 -j ACCEPT")

  general.shell_exec("service iptables save")
  #iptables.iptables(" --list")

def _install_cobbler():
  #
  # Install cobbler
  #
  # See http://linux.die.net/man/1/cobbler
  # See https://fedorahosted.org/cobbler/wiki/DownloadInstructions
  # See https://fedorahosted.org/cobbler/wiki/UsingCobblerImport
  # See http://www.ithiriel.com/content/2010/02/22/installing-linux-vms-under-kvm-cobbler-and-koan

  # To get cobbler and kvm work correct.
  general.shell_exec("yum -y install qspice-libs yum-utils cobbler koan httpd dhcp")
  general.shell_exec("chkconfig httpd on")

  # This allows the Apache httpd server to connect to the network
  general.shell_exec('/usr/sbin/setsebool -P httpd_can_network_connect true')
  general.shell_exec('/usr/sbin/semanage fcontext -a -t public_content_t "/tftpboot/.*"')
  general.shell_exec('/usr/sbin/semanage fcontext -a -t public_content_t "/var/www/cobbler/images/.*"')
  # Eventually if /var/www/cobbler/images wasn't set by above.
  #chcon -R -t public_content_t "/var/www/cobbler/images/.*"
  # Dont exist?? /usr/sbin/semanage fcontext -a -t httpd_sys_content_rw_t "/var/lib/cobbler/webui_sessions/.*"

  app.print_verbose("Update xinetd config files")
  general.set_config_property("/etc/xinetd.d/tftp", '[\s]*disable[\s]*[=].*', "        disable                 = no")
  general.set_config_property("/etc/xinetd.d/rsync", '[\s]*disable[\s]*[=].*', "        disable         = no")
  general.shell_exec("/etc/init.d/xinetd restart")

def _modify_coppler_settings():
  app.print_verbose("Update cobbler config files")
  general.set_config_property("/etc/cobbler/settings", '^server:.*', "server: " + app.get_installation_server_ip())
  general.set_config_property("/etc/cobbler/settings", '^next_server:.*', "next_server: " + app.get_installation_server_ip())
  general.set_config_property("/etc/cobbler/settings", '^default_virt_bridge:.*', "default_virt_bridge: br1")
  general.set_config_property("/etc/cobbler/settings", '^default_password_crypted:.*', "default_password_crypted: " + app.get_root_password_hash())
  general.set_config_property("/etc/cobbler/settings", '^default_virt_type:.*', "default_virt_type: qemu")
  general.set_config_property("/etc/cobbler/settings", '^anamon_enabled:.*', "anamon_enabled: 1")
  general.set_config_property("/etc/cobbler/settings", '^yum_post_install_mirror:.*', "yum_post_install_mirror: 1")
  general.set_config_property("/etc/cobbler/settings", '^manage_dhcp:.*', "manage_dhcp: 1")

  shutil.copyfile(app.SYCO_PATH + "/var/kickstart/host.ks", "/var/lib/cobbler/kickstarts/host.ks")
  shutil.copyfile(app.SYCO_PATH + "/var/kickstart/guest.ks", "/var/lib/cobbler/kickstarts/guest.ks")
  shutil.copyfile(app.SYCO_PATH + "/var/dhcp/dhcp.template", "/etc/cobbler/dhcp.template")

  # Config crontab to update repo automagically
  general.set_config_property("/etc/crontab", "01 \* \* \* \* root cobbler reposync \-\-tries\=3 \-\-no\-fail", "01 * * * * root cobbler reposync --tries=3 --no-fail")

  # Set apache servername
  general.set_config_property("/etc/httpd/conf/httpd.conf", "#ServerName www.example.com:80", "ServerName " + app.get_installation_server() + ":80")

  general.shell_exec("/etc/init.d/httpd restart")
  # TODO: Do we need no_return=True
  # general.shell_exec("/etc/init.d/cobblerd restart", no_return=True)
  general.shell_exec("/etc/init.d/cobblerd restart")

  # Wait for cobblered to restart
  time.sleep(1)
  general.shell_exec("cobbler get-loaders")

  # Setup distro/repo for centos
  general.shell_exec("cobbler check")

def _import_repos():
  if (os.access("/var/www/cobbler/ks_mirror/centos5.5-x86_64", os.F_OK)):
    app.print_verbose("Centos5.5-x86_64 already imported")
  else:
    general.shell_exec("cobbler import --path=rsync://ftp.sunet.se/pub/Linux/distributions/centos/5.5/os/x86_64/ --name=centos5.5 --arch=x86_64")

  if (os.access("/var/www/cobbler/repo_mirror/centos5-updates-x86_64", os.F_OK)):
    app.print_verbose("Centos5-updates-x86_64 repo already imported")
  else:
    general.shell_exec("cobbler repo add --arch=x86_64 --name=centos5-updates-x86_64 --mirror=rsync://ftp.sunet.se/pub/Linux/distributions/centos/5.5/updates/x86_64/")
    general.shell_exec("cobbler reposync")

  general.shell_exec("cobbler distro remove --name centos5.5-xen-x86_64")
  general.shell_exec("cobbler profile remove --name centos5.5-x86_64")

def _refresh_all_profiles():
  # Setup installation profiles and systems
  general.shell_exec("cobbler profile remove --name=centos5.5-vm_guest")
  general.shell_exec("""cobbler profile add --name=centos5.5-vm_guest \
      --distro=centos5.5-x86_64 --virt-type=qemu \
      --virt-ram=1024 --virt-cpus=1 \
      --repos="centos5-updates-x86_64" \
      --kickstart=/var/lib/cobbler/kickstarts/guest.ks \
      --virt-bridge=br1""")

  general.shell_exec("cobbler profile remove --name=centos5.5-vm_host")
  general.shell_exec("""cobbler profile add --name=centos5.5-vm_host \
    --distro=centos5.5-x86_64 \
    --repos="centos5-updates-x86_64" \
    --kickstart=/var/lib/cobbler/kickstarts/host.ks""")

def _cobbler_sync():
  general.shell_exec("cobbler sync")
  general.shell_exec("cobbler report")

def _remove_all_systems():
  stdout = general.shell_exec("cobbler system list")
  for name in stdout.rsplit():
    general.shell_exec("cobbler system remove --name " + name)

def _host_add(host_name, ip):
  mac = app.get_mac(host_name)
  general.shell_exec("cobbler system add --profile=centos5.5-vm_host " +
                     "--static=1 --gateway=10.100.0.1 --subnet=255.255.0.0 " +
                     "--name=" + host_name + " --hostname=" + host_name + " --ip=" + str(ip) + " " +
                     "--mac=" + mac)

def _guest_add(host_name, ip):
  disk_var = app.get_disk_var(host_name)
  disk_var = int(disk_var) * 1024
  ram = app.get_ram(host_name)
  cpu = app.get_cpu(host_name)

  general.shell_exec("cobbler system add --profile=centos5.5-vm_guest "
                     "--static=1 --gateway=10.100.0.1 --subnet=255.255.0.0 " +
                     "--virt-path=\"/dev/VolGroup00/" + host_name + "\" " +
                     "--virt-ram=" + str(ram) + " --virt-cpus=" + str(cpu) + " " +
                     "--name=" + host_name + " --hostname=" + host_name + " --ip=" + str(ip) + " " +
                     "--ksmeta=\"disk_var=" + str(disk_var) + "\"")