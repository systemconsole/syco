#! /usr/bin/env python

# This script will harden an centos minium installation
#
# For more information see:
# http://www.linuxforums.org/forum/red-hat-fedora-linux/166631-redhat-centos-hardening-customizing-removing-excess.html
# http://www.nsa.gov/ia/_files/factshe...phlet-i731.pdf
# http://wiki.centos.org/HowTos/OS_Protection
#
# Changelog
# 101005 DL - Draft
# 101128 DL - Included in fosh

import sys, os, fileinput, re, shlex, subprocess

import app, general

# The main function
#   
def run():    
    #user_add()
    enable_selinux()
    disable_services()
    disable_virtual_terminals()
    remove_rpms()
    customize_shell()
    hardening()
    clear_login_screen()
    yum_update()   
    disable_ip6_support()

#def user_add():
#  app.print_verbose('User add')
#  
#  name = ""
#  while name == "":
#    name = raw_input("User name:")
#  
#  general.shell_exec("useradd " + name + " -G wheel,root")
#  error while general.shell_exec("passwd " + name):
#    pass
#    
#  general.shell_exec("chmod +w /etc/sudoers")
#  general.set_config_property("/etc/sudoers",'^# %wheel.*ALL=\(ALL\).*ALL$',"%wheel        ALL=(ALL)       ALL")
#  general.shell_exec("chmod 0440 /etc/sudoers")     
#  
#  process = subprocess.Popen('visudo -c', shell=True, stdout=subprocess.PIPE)
#  if process.communicate()[0][:-1] != "/etc/sudoers: parsed OK":
#    app.print_error("/etc/sudoers is not ok")
#    sys.exit()  

def enable_selinux():
  '''
  All machines should have selinux on by default.
  For more info: http://www.crypt.gen.nz/selinux/disable_selinux.html
  '''    
  app.print_verbose("Enable SELinux")
  if (general.grep("/etc/selinux/config", "SELINUX=enforcing") or 
      general.grep("/etc/selinux/config", "SELINUX=permissive")):
    general.set_config_property("/etc/selinux/config", '^SELINUX=.*$',     "SELINUX=enforcing")
    general.set_config_property("/etc/selinux/config", '^SELINUXTYPE=.*$', "SELINUXTYPE=targeted")
  else:
    app.print_error("SELinux is disabled, more need to be done, read http://www.crypt.gen.nz/selinux/disable_selinux.html")

def disable_services():
  '''
  Turn of autostart of services that are not used, and dont need to be used
  on a default centos server.
  
  Which services are autostarted
  chkconfig  --list |grep on
  
  Which services are autostarted in level 3
  chkconfig --list |grep "3:on" |awk '{print $1}' |sort
  
  What status has the services, started/stopped?
  /sbin/service --status-all
  
  For more info:
  http://www.sonoracomm.com/support/18-support/114-minimal-svcs
  http://www.imminentweb.com/technologies/centos-disable-unneeded-services-boot-time
  http://magazine.redhat.com/2007/03/09/understanding-your-red-hat-enterprise-linux-daemons/  
  '''
  app.print_verbose("Disable services")
  disable_service("anacron")
  disable_service("atd")
  disable_service("hidd")
  disable_service("cpuspeed")
  disable_service("cups")
  disable_service("gpm")
  disable_service("yum-updatesd") 
  disable_service("portmap")
  disable_service("sendmail")
  disable_service("mcstrans")
  disable_service("pcscd")
  disable_service("nfslock")
  disable_service("netfs")
  disable_service("ip6tables")
  disable_service("bluetooth")
  disable_service("avahi-daemon")
  disable_service("autofs")
  disable_service("readahead_early")
  disable_service("rpcgssd")
  disable_service("rpcidmapd")
  disable_service("firstboot")
  disable_service("rawdevices")
  disable_service("mdmonitor")

def disable_virtual_terminals():
  '''
  Minimize use of memory, and disable possiblity to forget a tty logged in 
  when leaving the machine.
  '''
  app.print_verbose("Disable virtual terminals")
  general.set_config_property("/etc/inittab", "^[#]?2:2345:respawn:/sbin/mingetty tty2$","#2:2345:respawn:/sbin/mingetty tty2")
  general.set_config_property("/etc/inittab", "^[#]?3:2345:respawn:/sbin/mingetty tty3$","#3:2345:respawn:/sbin/mingetty tty3")
  general.set_config_property("/etc/inittab", "^[#]?4:2345:respawn:/sbin/mingetty tty4$","#4:2345:respawn:/sbin/mingetty tty4")
  general.set_config_property("/etc/inittab", "^[#]?5:2345:respawn:/sbin/mingetty tty5$","#5:2345:respawn:/sbin/mingetty tty5")
  general.set_config_property("/etc/inittab", "^[#]?6:2345:respawn:/sbin/mingetty tty6$","#6:2345:respawn:/sbin/mingetty tty6")
    
def remove_rpms():
  '''Remove rpms that are not used on our default installations'''
  app.print_verbose("Remove rpms")
  rpm_remove("unix2dos-2.2-26.2.3.el5")
  rpm_remove("mkbootdisk-1.5.3-2.1.x86_64")
  rpm_remove("dosfstools-2.11-7.el5")
  rpm_remove("dos2unix-3.1-27.2.el5")
  rpm_remove("finger-0.17-32.2.1.1")
  rpm_remove("firstboot-tui-1.4.27.7-1.el5.centos")

def customize_shell():
  app.print_verbose("Customize shell")
  
  print "   Add Date And Time To History Output"
  general.set_config_property("/etc/bashrc", "^export HISTTIMEFORMAT=.*$","export HISTTIMEFORMAT=\"%h/%d - %H:%M:%S \"")
  
  print "   Add Color To Grep"
  general.set_config_property("/root/.bash_profile", "^export GREP_COLOR=.*$","export GREP_COLOR='1;32'")
  general.set_config_property("/root/.bash_profile", "^export GREP_OPTIONS=.*$","export GREP_OPTIONS=--color=auto")
  general.set_config_property("/etc/skel/.bash_profile", "^export GREP_COLOR=.*$","export GREP_COLOR='1;32'")
  general.set_config_property("/etc/skel/.bash_profile", "^export GREP_OPTIONS=.*$","export GREP_OPTIONS=--color=auto")

def hardening():
  app.print_verbose("Hardening")
  
  app.print_verbose("   Disable usb drives.")
  general.set_config_property("/etc/modprobe.d/blacklist-usbstorage", "^blacklist usb-storage$", "blacklist usb-storage")
  
  # todo:
  #app.print_verbose("   Disallow Root Ssh Login (Must Su To Root)")
  #general.set_config_property("/etc/ssh/sshd_config", "^[#]*PermitRootLogin.*$", "PermitRootLogin no")
  
  app.print_verbose("   Store passwords sha512 instead of md5")
  general.shell_exec("authconfig --passalgo=sha512 --update")
  
  app.print_verbose("   Help kernel to prevent certain kinds of attacks")
  general.set_config_property("/etc/sysctl.conf", "^net.ipv4.icmp_ignore_bogus_error_messages=.*$","net.ipv4.icmp_ignore_bogus_error_messages=1")
  general.set_config_property("/etc/sysctl.conf", "^kernel.exec-shield=.*$","kernel.exec-shield=1")
  general.set_config_property("/etc/sysctl.conf", "^kernel.randomize_va_space=.*$","kernel.randomize_va_space=1")
  general.set_config_property("/etc/sysctl.conf", "^net.ipv4.icmp_echo_ignore_broadcasts=.*$","net.ipv4.icmp_echo_ignore_broadcasts=1")

def clear_login_screen():
  '''Clear information shown on the console login screen.'''
  general.shell_exec("clear > /etc/issue")
  general.shell_exec("clear > /etc/issue.net")

def yum_update():
  app.print_verbose("Update with yum")
  general.shell_exec("yum update -y")

def disable_ip6_support():
  app.print_verbose("Disable IP6 support")
  general.set_config_property("/etc/modprobe.conf", "^alias ipv6 off$","alias ipv6 off")
  general.set_config_property("/etc/modprobe.conf", "^alias net-pf-10 off$","alias net-pf-10 off")
  general.set_config_property("/etc/sysconfig/network", "^NETWORKING_IPV6=.*$","NETWORKING_IPV6=no")
  general.shell_exec("service network restart")

#
# Helper functions
#

def disable_service(name):
  '''Disable autostartup of a service and stop the service'''
  process = subprocess.Popen('chkconfig --list |grep "3:on" |awk \'{print $1}\' |grep ' + name, shell=True, stdout=subprocess.PIPE)
  if (process.communicate()[0][:-1] == name):
    subprocess.call(["chkconfig", name,  "off"])
    app.print_verbose("   chkconfig " + name + " off")

  process=subprocess.Popen('service ' + name + ' status', shell=True, stdout=subprocess.PIPE)
  result=process.communicate()[0][:-1]
  if ("stopped" not in result and
      "not running" not in result
      ):
    subprocess.call(["/sbin/service", name, "stop"])
    app.print_verbose("   service " + name + " stop")
     
def rpm_remove(name):
  '''Remove rpm packages'''
  process=subprocess.Popen('rpm -q ' + name, shell=True, stdout=subprocess.PIPE)
  if process.communicate()[0][:-1] != "package " + name + " is not installed":
    general.shell_exec("rpm -e " + name)        
