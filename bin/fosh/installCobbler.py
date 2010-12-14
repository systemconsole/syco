#! /usr/bin/env python

import socket, shutil, time, os
import app, general, version, iptables

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("install-cobbler", install_cobbler, help="Install cobbler on the current server.")

def install_cobbler(args):
  '''
  Install cobbler on current host
  
  '''  
  global script_version
  app.print_verbose("Install cobbler version: %d" % script_version)
  ver_obj = version.Version()
  if ver_obj.is_executed("install_cobbler", script_version):
    app.print_verbose("   Already installed latest version")
    return

  install_epel_repo()
  setup_firewall()
  install_cobbler()
  modify_coppler_settings()
  import_repos()
  setup_all_systems()
  cobbler_sync
  ver_obj.mark_executed("install_cobbler", script_version)
    
def install_epel_repo():
  '''
  Setup EPEL repository.
    
  Need the EPEL repos for cobbler and koan
  http://ridingthecloud.com/installing-epel-repository-centos-rhel/
  http://www.question-defense.com/2010/04/22/install-the-epel-repository-on-centos-linux-5-x-epel-repo
  
  '''  
  result, err = general.shell_exec("rpm -q epel-release-5-4.noarch")
  if "package epel-release-5-4.noarch is not installed" in result:    
    general.shell_exec("rpm -Uhv http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm")
    app.print_verbose("(Don't mind the Header V3 DSA warning)")

def setup_firewall():
  #  
  # Setup firewall
  #
    
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
  
def install_cobbler():
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
  general.set_config_property("/etc/xinetd.d/tftp", '[\s]*disable[\s]*[=].*',     "        disable                 = no")  
  general.set_config_property("/etc/xinetd.d/rsync", '[\s]*disable[\s]*[=].*',     "        disable         = no")  
  general.shell_exec("/etc/init.d/xinetd restart") 

def modify_coppler_settings(): 
  app.print_verbose("Update cobbler config files")  
  general.set_config_property("/etc/cobbler/settings", '^server:.*',                    "server: " + app.get_ip("fo-tp-install"))
  general.set_config_property("/etc/cobbler/settings", '^next_server:.*',               "next_server: " + app.get_ip("fo-tp-install"))
  general.set_config_property("/etc/cobbler/settings", '^default_virt_bridge:.*',       "default_virt_bridge: br1")  
  general.set_config_property("/etc/cobbler/settings", '^default_password_crypted:.*',  "default_password_crypted: " + app.get_root_password())
  general.set_config_property("/etc/cobbler/settings", '^default_virt_type:.*',         "default_virt_type: qemu")  
  general.set_config_property("/etc/cobbler/settings", '^anamon_enabled:.*',            "anamon_enabled: 1")  
  general.set_config_property("/etc/cobbler/settings", '^yum_post_install_mirror:.*',   "yum_post_install_mirror: 1")  
  general.set_config_property("/etc/cobbler/settings", '^manage_dhcp:.*',               "manage_dhcp: 1")  

  shutil.copyfile(app.fosh_path + "/var/fo-tp-host.ks", "/var/lib/cobbler/kickstarts/fo-tp-host.ks")
  shutil.copyfile(app.fosh_path + "/var/fo-tp-guest.ks", "/var/lib/cobbler/kickstarts/fo-tp-guest.ks")
  shutil.copyfile(app.fosh_path + "/var/fo-tp-install/dhcp.template", "/etc/cobbler/dhcp.template")

  # Config crontab to update repo automagically
  general.set_config_property("/etc/crontab", "01 \* \* \* \* root cobbler reposync \-\-tries\=3 \-\-no\-fail", "01 * * * * root cobbler reposync --tries=3 --no-fail")

  # Set apache servername
  general.set_config_property("/etc/httpd/conf/httpd.conf", "#ServerName www.example.com:80", "ServerName fo-tp-install:80")

  general.shell_exec("/etc/init.d/httpd restart")
  general.shell_exec("/etc/init.d/cobblerd restart", no_return=True)
  
  # Wait for cobblered to restart
  time.sleep(1)
  general.shell_exec("cobbler get-loaders")
  
  # Setup distro/repo for centos
  general.shell_exec("cobbler check")

def import_repos():  
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
  
  # Setup installation profiles and systems
  general.shell_exec("cobbler profile remove --name=centos5.5-x86_64")
  general.shell_exec("""cobbler profile add --name=centos5.5-vm_guest \
      --distro=centos5.5-x86_64 --virt-type=qemu \
      --virt-ram=1024 --virt-cpus=1 \
      --repos="centos5-updates-x86_64" \
      --kickstart=/var/lib/cobbler/kickstarts/fo-tp-guest.ks \
      --virt-bridge=br1""")     
  
  general.shell_exec("""cobbler profile add --name=centos5.5-vm_host \
    --distro=centos5.5-x86_64 \
    --repos="centos5-updates-x86_64" \
    --kickstart=/var/lib/cobbler/kickstarts/fo-tp-host.ks""")
  
def setup_all_systems():
  
  # Check thease cobbler settings
  # --dns-name  

  remove_all_systems()
  for host_name in app.get_servers():
    ip=app.get_ip(host_name)
    ram=app.get_ip(host_name)
    cpu=app.get_ip(host_name)
    if (len(app.get_guests(host_name))):
      mac=app.get_mac(host_name)
      app.print_verbose("Install host " + host_name + " with ip " + ip + " and mac " + mac)
      host_add(host_name, ip, mac, ram, cpu)
    else:
      app.print_verbose("Install guest " + host_name + " with ip " + ip)
      guest_add(host_name, ip, ram, cpu)

def cobbler_sync():
  general.shell_exec("cobbler sync")
  general.shell_exec("cobbler report")
  
def host_add(name, ip, mac, ram=1024, cpu=1):
  general.shell_exec("cobbler system add --profile=centos5.5-vm_host " +
      "--static=1 --gateway=10.100.0.1 --subnet=255.255.0.0 " +
      "--name=" + name + " --hostname=" + name + " --ip=" + str(ip) + " " +
      "--virt-ram=" + str(ram) + " --virt-cpus= " + str(cpu) + " " +
      "--mac=" + mac)

def guest_add(name, ip, ram=1024, cpu=1):
  disk_var=app.get_disk_var(name)
  disk_var=int(disk_var)*1024
  
  general.shell_exec("cobbler system add --profile=centos5.5-vm_guest " 
      "--static=1 --gateway=10.100.0.1 --subnet=255.255.0.0 " +
      "--virt-path=\"/dev/VolGroup00/" + name + "\" " +
      "--virt-ram=" + str(ram) + " --virt-cpus= " + str(cpu) + " " +      
      "--name=" + name + " --hostname=" + name + " --ip=" + str(ip) + " " +
      "--ksmeta=\"disk_var=" + str(disk_var) + "\"") 

def remove_all_systems():
  stdout, stderr = general.shell_exec("cobbler system list")
  for name in stdout.rsplit():
    general.shell_exec("cobbler system remove --name " + name)
               
def install_guests(): 
  install_epel_repo()
  general.shell_exec("yum -y install koan")

  # Wait to install guests until fo-tp-install is alive.
  while (not is_fo_tp_install_alive()):
    app.print_error("fo-tp-install is not alive, try again in 15 seconds.")
    time.sleep(15)

  guests={}
  installed={}
  host_name=socket.gethostname()
  for guest_name in app.get_guests(host_name):
    if (is_guest_installed(guest_name, options="")):
      app.print_verbose(guest_name + " already installed", 2)
    else:
      guests[guest_name]= host_name
            
  for guest_name, host_name in guests.items():
    if (not is_guest_installed(guest_name)):
      install_guest(host_name, guest_name)
        
  # Wait for the installation process to finish,
  # And start the quests.  
  while(len(guests)):    
    time.sleep(5)
  
    for guest_name, host_name in guests.items():
      if (_start_guest(guest_name)):
        del guests[guest_name]
              
def install_guest(host_name, guest_name):
  app.print_verbose("Install " + guest_name + " on " + host_name)

  # Create the data lvm volumegroup
  result, err=general.shell_exec("lvdisplay -v /dev/VolGroup00/" + guest_name, error=False)
  if ("/dev/VolGroup00/" + guest_name not in result):
    disk_var_size=int(app.get_disk_var(guest_name))
    disk_used_by_other_log_vol=15
    extra_not_used_space=5
    vol_group_size=disk_var_size+disk_used_by_other_log_vol+extra_not_used_space
    general.shell_exec("lvcreate -n " + guest_name + " -L " + str(vol_group_size) + "G VolGroup00")
  
  general.shell_exec("koan --server=10.100.100.200 --virt --system=" + guest_name)
  general.shell_exec("virsh autostart " + guest_name)

def _start_guest(guest_name):
  '''
  Wait for guest to be halted, before starting it.
  
  '''
  if (is_guest_installed(guest_name, options="")):
    return False
  else:
    general.shell_exec("virsh start " + guest_name)
    return True
  
def is_guest_installed(guest_name, options="--all"):
  '''
  Is the guest already installed on the kvm host.
  
  '''
  result, err = general.shell_exec("virsh list " + options)
  if (guest_name in result):    
    return True
  else:
    return False  
        
def is_fo_tp_install_alive():
  return general.is_server_alive("10.100.100.200", 22)  