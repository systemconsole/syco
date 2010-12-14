#! /usr/bin/env python

# Install the server to act as a openvpn server
#
# Will use 10.100.10.0:1194 as the vpn client net
# 
# More info about openvpn.
# http://openvpn.net/index.php/open-source/documentation/howto.html
# http://notes.brooks.nu/2008/08/openvpn-setup-on-centos-52/
# http://www.howtoforge.com/openvpn-server-on-centos-5.2
# http://www.throx.net/2008/04/13/openvpn-and-centos-5-installation-and-configuration-guide/

import os, subprocess, time, pexpect, stat
import app, general, version, iptables

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("install-openvpn-server", install_openvpn_server, help="Install openvpn-server on the current server.")
  commands.add("install-openvpn-client-certs", build_client_certs, help="Build client certs on the openvpn server.")

def install_openvpn_server(args):
  '''
  The actual installation of openvpn server.
  
  '''
  global script_version
  app.print_verbose("Install openvpn server version: %d" % script_version)
  ver_obj = version.Version()
  if ver_obj.is_executed("InstallOpenvpnServer", script_version):
    app.print_verbose("   Already installed latest version")
    return

  general.shell_exec("yum -y install openvpn")

  general.shell_exec("cp -R /usr/share/openvpn/easy-rsa/2.0 /etc/openvpn/easy-rsa")
  general.shell_exec("cp " + app.fosh_path + "/var/openvpn/server.conf /etc/openvpn/server.conf")

  # Prepare the ca cert generation.
  general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_COUNTRY.*',  'export KEY_COUNTRY="SE"')
  general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_PROVINCE.*', 'export KEY_PROVINCE="NA"')
  general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_CITY.*',     'export KEY_CITY="STOCKHOLM"')
  general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_ORG.*',      'export KEY_ORG="FAREOFFICE"')
  general.set_config_property("/etc/openvpn/easy-rsa/vars", '[\s]*export KEY_EMAIL.*',    'export KEY_EMAIL="ssladmin@fareoffice.com"')

  # Generate CA cert
  os.chdir("/etc/openvpn/easy-rsa/")
  general.shell_exec(". ./vars;./clean-all;./build-ca --batch;./build-key-server --batch server;./build-dh")
  general.shell_exec("cp /etc/openvpn/easy-rsa/keys/{ca.crt,ca.key,server.crt,server.key,dh1024.pem} /etc/openvpn/")

  # To be able to route trafic to internal network
  general.set_config_property("/etc/sysctl.conf", '[\s]*net.ipv4.ip_forward[\s]*[=].*', "net.ipv4.ip_forward = 1")
  general.shell_exec("echo 1 > /proc/sys/net/ipv4/ip_forward")  
  iptables.iptables("-t nat -A POSTROUTING -s 10.100.10.0/24 -o eth0 -j MASQUERADE")
  iptables.iptables("-I INPUT 1 -m state --state NEW -m tcp -p tcp --dport 1194 -j ACCEPT")
  
  # To protect the network.
  iptables.iptables("-A FORWARD -i tun0 -s 10.100.10.0/24 -o eth0 -j ACCEPT")
  iptables.iptables('-A FORWARD -i eth0 -o tun0 -m state --state "ESTABLISHED,RELATED" -j ACCEPT')
  general.shell_exec("service iptables save")  

  general.shell_exec("/etc/init.d/openvpn restart")
  general.shell_exec("chkconfig openvpn on")
  
  build_client_certs(args)
    
  ver_obj.mark_executed("InstallOpenvpnServer", script_version)
  
def build_client_certs(args):
  os.chdir("/etc/openvpn/easy-rsa/keys")
  general.set_config_property("/etc/cronjob", "01 * * * * root run-parts fosh build_client_certs", "01 * * * * root run-parts fosh build_client_certs")
  general.shell_exec("cp " + app.fosh_path + "/var/openvpn/client.conf ./client.conf")
  general.shell_exec("cp " + app.fosh_path + "/doc/openvpn/install.txt .")
  
  for user in os.listdir("/home"):
    cert_already_installed=os.access("/home/" + user +"/openvpn_client_keys.zip", os.F_OK)
    valid_file="lost+found" not in user
    if valid_file and not cert_already_installed:
      os.chdir("/etc/openvpn/easy-rsa/")
      general.set_config_property("/etc/openvpn/easy-rsa/build-key-pkcs12", '.*export EASY_RSA.*', 'source ./vars;export EASY_RSA="${EASY_RSA:-.}"')
                  
      out = pexpect.run("./build-key-pkcs12 --batch " + user, 
        cwd="/etc/openvpn/easy-rsa/", 
        events={'(?i)Enter Export Password:':'\n', '(?i)Verifying - Enter Export Password:':'\n'}
      )
      app.print_verbose(out)
      

      # Config client.crt      
      general.set_config_property("/etc/openvpn/easy-rsa/keys/client.conf", "^cert.*crt", "cert " + user + ".crt")
      general.set_config_property("/etc/openvpn/easy-rsa/keys/client.conf", "^key.*key", "key " + user + ".key")

      os.chdir("/etc/openvpn/easy-rsa/keys")
      general.shell_exec("zip /home/" + user +"/openvpn_client_keys.zip ca.crt " + user + ".crt " + user + ".key " + user + ".p12 client.conf install.txt")
      # Set permission for the user who now owns the file.
      os.chmod("/home/" + user +"/openvpn_client_keys.zip", stat.S_IRUSR | stat.S_IRGRP)
      pexpect.run("chown " + user + ":" + user + " /home/" + user +"/openvpn_client_keys.zip ")

# TODO/OTHER
# yum installopenvpn-auth-ldap ??