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
import config
import general
import iptables
import version
import install

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 2

def build_commands(commands):
  commands.add("install-cobbler",        install_cobbler, help="Install cobbler on the current server.")
  commands.add("install-cobbler-config", setup_all_systems, help="Refresh install.cfg settings to cobbler.")
  commands.add("install-cobbler-repo",   refresh_repo, help="Refresh all repos on the cobbler server.")

def install_cobbler(args):
  '''
  Install cobbler on current host.

  '''
  app.print_verbose("Install cobbler version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("installCobbler", SCRIPT_VERSION)
  version_obj.check_executed()

  # Initialize password.
  app.get_root_password_hash()

  _install_cobbler()

  iptables.add_cobbler_chain()
  iptables.save()

  _modify_cobbler_settings()
  _import_repos()
  setup_all_systems(args)
  _cobbler_sync
  version_obj.mark_executed()

def setup_all_systems(args):
  '''
  Update cobbler with all settings in install.cfg.

  '''
  _refresh_all_profiles()
  _remove_all_systems()
  for hostname in config.get_servers():
    # IS KVM host?
    if (config.host(hostname().is_host()):
      _host_add(hostname)
    else:
      _guest_add(hostname)

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
  downloads['jdk-6u25-linux-x64-rpm.bin'] = 'http://cds.sun.com/is-bin/INTERSHOP.enfinity/WFS/CDS-CDS_Developer-Site/en_US/-/USD/VerifyItem-Start/jdk-6u24-linux-x64-rpm.bin?BundledLineItemUUID=pGSJ_hCvabIAAAEu870pGPfd&OrderID=1ESJ_hCvsh4AAAEu1L0pGPfd&ProductID=oSKJ_hCwOlYAAAEtBcoADqmS&FileName=/jdk-6u25-linux-x64-rpm.bin'
  downloads['jdk-6u26-linux-x64-rpm.bin'] = 'http://cds.sun.com/is-bin/INTERSHOP.enfinity/WFS/CDS-CDS_Developer-Site/en_US/-/USD/VerifyItem-Start/jdk-6u24-linux-x64-rpm.bin?BundledLineItemUUID=pGSJ_hCvabIAAAEu870pGPfd&OrderID=1ESJ_hCvsh4AAAEu1L0pGPfd&ProductID=oSKJ_hCwOlYAAAEtBcoADqmS&FileName=/jdk-6u26-linux-x64-rpm.bin'

  for dst, src in downloads.items():
    general.shell_exec("wget --background -O /var/www/cobbler/repo_mirror/" + dst + " "  + src)

  while(True):
    num_of_processes = subprocess.Popen("ps aux | grep wget", stdout=subprocess.PIPE, shell=True).communicate()[0].count("\n")
    if num_of_processes <=2:
      break
    app.print_verbose(str(num_of_processes-2) + " processes running, wait 10 more sec.")
    time.sleep(10)

  general.shell_exec("cobbler reposync --tries=3 --no-fail")
  general.shell_exec("cobbler sync")

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
  general.shell_exec("/sbin/chkconfig httpd on")
  general.shell_exec("/sbin/chkconfig dhcpd on")

  # This allows the Apache httpd server to connect to the network
  general.shell_exec('/usr/sbin/semanage fcontext -a -t public_content_rw_t "/tftpboot/.*"')
  general.shell_exec('/usr/sbin/semanage fcontext -a -t public_content_rw_t "/var/www/cobbler/images/.*"')
  general.shell_exec('restorecon -R -v "/tftpboot/"')
  general.shell_exec('restorecon -R -v "/var/www/cobbler/images.*"')

  # Enables cobbler to read/write public_content_rw_t
  general.shell_exec('/usr/sbin/setsebool -P cobbler_anon_write on')

  # Enable httpd to connect to cobblerd (optional, depending on if web interface is installed)
  # Notice: If you enable httpd_can_network_connect_cobbler and you should switch httpd_can_network_connect off
  general.shell_exec('/usr/sbin/setsebool -P httpd_can_network_connect off')
  general.shell_exec('/usr/sbin/setsebool -P httpd_can_network_connect_cobbler on')

  #Enabled cobbler to use rsync etc.. (optional)
  general.shell_exec('/usr/sbin/setsebool c-Pobbler_can_network_connect on')

  #Enable cobbler to use CIFS based filesystems (optional)
  #general.shell_exec('/usr/sbin/setsebool -P cobbler_use_cifs on')

  # Enable cobbler to use NFS based filesystems (optional)
  #general.shell_exec('/usr/sbin/setsebool -P cobbler_use_nfs on')

  # Double check your choices
  general.shell_exec('getsebool -a|grep cobbler')

  app.print_verbose("Update xinetd config files")
  general.set_config_property("/etc/xinetd.d/tftp", '[\s]*disable[\s]*[=].*', "        disable                 = no")
  general.set_config_property("/etc/xinetd.d/rsync", '[\s]*disable[\s]*[=].*', "        disable         = no")
  general.shell_exec("/etc/init.d/xinetd restart")

def _modify_cobbler_settings():
  app.print_verbose("Update cobbler config files")
  general.set_config_property("/etc/cobbler/settings", '^server:.*', "server: " + config.general.get_installation_server_ip())
  general.set_config_property("/etc/cobbler/settings", '^next_server:.*', "next_server: " + config.general.get_installation_server_ip())
  general.set_config_property("/etc/cobbler/settings", '^default_virt_bridge:.*', "default_virt_bridge: br0")
  general.set_config_property("/etc/cobbler/settings", '^default_password_crypted:.*', "default_password_crypted: " + app.get_root_password_hash())
  general.set_config_property("/etc/cobbler/settings", '^default_virt_type:.*', "default_virt_type: qemu")
  general.set_config_property("/etc/cobbler/settings", '^anamon_enabled:.*', "anamon_enabled: 1")
  general.set_config_property("/etc/cobbler/settings", '^yum_post_install_mirror:.*', "yum_post_install_mirror: 1")
  general.set_config_property("/etc/cobbler/settings", '^manage_dhcp:.*', "manage_dhcp: 1")

  shutil.copyfile(app.SYCO_PATH + "/var/kickstart/host.ks", "/var/lib/cobbler/kickstarts/host.ks")
  shutil.copyfile(app.SYCO_PATH + "/var/kickstart/guest.ks", "/var/lib/cobbler/kickstarts/guest.ks")

  # Configure DHCP
  shutil.copyfile(app.SYCO_PATH + "/var/dhcp/dhcp.template", "/etc/cobbler/dhcp.template")
  general.shell_exec("/etc/init.d/dhcpd restart")

  # Config crontab to update repo automagically
  value="01 4 * * * syco install-cobbler-repo"
  general.set_config_property("/etc/crontab", value, value)

  # Set apache servername
  general.set_config_property("/etc/httpd/conf/httpd.conf", "#ServerName www.example.com:80", "ServerName " + config.general.get_installation_server() + ":80")

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
  if (os.access("/var/www/cobbler/ks_mirror/centos-x86_64", os.F_OK)):
    app.print_verbose("Centos-x86_64 already imported")
  else:
    general.shell_exec("cobbler import --path=rsync://ftp.sunet.se/pub/Linux/distributions/centos/6/os/x86_64/ --name=centos --arch=x86_64")

  if (os.access("/var/www/cobbler/repo_mirror/centos-updates-x86_64", os.F_OK)):
    app.print_verbose("Centos-updates-x86_64 repo already imported")
  else:
    general.shell_exec("cobbler repo add --arch=x86_64 --name=centos-updates-x86_64 --mirror=rsync://ftp.sunet.se/pub/Linux/distributions/centos/6/updates/x86_64/")
    general.shell_exec("cobbler repo add --arch=x86_64 --name=EPEL-x86_64 --mirror=http://download.fedora.redhat.com/pub/epel/6/x86_64")
    general.shell_exec("cobbler reposync")

def _refresh_all_profiles():
  # Removed unused distros/profiles
  general.shell_exec("cobbler distro remove --name centos-xen-x86_64")
  general.shell_exec("cobbler profile remove --name centos-x86_64")

  # Setup installation profiles and systems
  general.shell_exec("cobbler profile remove --name=centos-vm_host")
  general.shell_exec(
    'cobbler profile add --name=centos-vm_host' +
    ' --distro=centos-x86_64' +
    ' --repos="centos-updates-x86_64"' +
    ' --kickstart=/var/lib/cobbler/kickstarts/host.ks'
  )

  general.shell_exec("cobbler profile remove --name=centos-vm_guest")
  general.shell_exec(
    'cobbler profile add --name=centos-vm_guest' +
    ' --distro=centos-x86_64 --virt-type=qemu' +
    ' --virt-ram=1024 --virt-cpus=1' +
    ' --repos="centos-updates-x86_64"' +
    ' --kickstart=/var/lib/cobbler/kickstarts/guest.ks' +
    ' --virt-bridge=br0'
  )

def _cobbler_sync():
  general.shell_exec("cobbler sync")
  general.shell_exec("cobbler report")

def _remove_all_systems():
  stdout = general.shell_exec("cobbler system list")
  for name in stdout.rsplit():
    general.shell_exec("cobbler system remove --name " + name)

def _host_add(hostname):
  app.print_verbose("Add " + hostname +
                    "(" + config.general.get_back_gateway_ip() + ")")

  general.shell_exec(
    "cobbler system add --profile=centos-vm_host " +
    "--name=" + hostname + " --hostname=" + hostname + " " +
    '--name-servers="' + config.general.get_front_resolver_ip() + '" ' +
    ' --ksmeta="disk_var=' + str(config.host(hostname).get_disk_var_mb()) +
    ' boot_device=' + str(config.host(hostname).get_boot_device("cciss/c0d0")) + '"')

  general.shell_exec(
    "cobbler system edit --name=" + hostname +
    " --interface=eth0 --static=1 " +
    " --ip=" + str(config.host(hostname).get_back_ip()) +
    " --mac=" + str(config.host(hostname).get_back_mac()) +
    " --gateway=" + config.general.get_back_gateway_ip() +
    " --subnet=" + config.general.get_back_netmask())

  general.shell_exec(
    "cobbler system edit --name=" + hostname +
    " --interface=eth1 --static=1 " +
    " --ip=" + str(config.host(hostname).get_front_ip()) +
    " --mac=" + str(config.host(hostname).get_front_mac()) +
    " --gateway=" + config.general.get_front_gateway_ip() +
    " --subnet=" + config.general.get_front_netmask())

def _guest_add(hostname):
  app.print_verbose("Add " + hostname +
                    "(" + config.general.get_back_gateway_ip() + ")")

  general.shell_exec(
    "cobbler system add --profile=centos-vm_guest"
    " --virt-path=\"/dev/VolGroup00/" + hostname + "\"" +
    " --virt-ram=" + str(config.host(hostname).get_ram()) +
    " --virt-cpus=" + str(config.host(hostname).get_cpu()) +
    " --name=" + hostname + " --hostname=" + hostname +
    ' --name-servers="' + config.general.get_front_resolver_ip() + '"' +
    ' --ksmeta="disk_var=' + str(config.host(hostname).get_disk_var_mb()) +
    ' boot_device=' + str(config.host(hostname).get_boot_device("hda")) + '"')

  general.shell_exec(
    "cobbler system edit --name=" + hostname +
    " --interface=eth0 --static=1 " +
    " --ip=" + str(config.host(hostname).get_back_ip()) +
    " --gateway=" + config.general.get_back_gateway_ip() +
    " --subnet=" + config.general.get_back_netmask())

  general.shell_exec(
    "cobbler system edit --name=" + hostname +
    " --interface=eth1 --static=1 " +
    " --ip=" + str(config.host(hostname).get_front_ip()) +
    " --gateway=" + config.general.get_front_gateway_ip() +
    " --subnet=" + config.general.get_front_netmask())
