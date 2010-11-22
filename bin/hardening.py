#! /usr/bin/env python

# This script will harden an centos minium installation
#
# For more information see:
# http://www.linuxforums.org/forum/red-hat-fedora-linux/166631-redhat-centos-hardening-customizing-removing-excess.html
# http://www.nsa.gov/ia/_files/factshe...phlet-i731.pdf
#
# Changelog
# 101005 DL - Draft

import sys, os, fileinput, re, shlex, subprocess

###

def grep(file, searchExp):       
    '''Do grep similar search on a file'''
    for line in open(file):
        if searchExp in line:
            print line        
            return True
    return False
    
###

def shell_exec(cmd):
    process = subprocess.Popen(shlex.split(cmd))
    return process.wait()

###

def print_label(name):
    '''Print a label for the configuration that should be done.'''
    print ""
    print name
    print "###################################"
    
###    
    
def set_config_property(file,searchExp,replaceExp):
    '''Change or add a config property to a specific value'''
    if os.path.exists(file):
        exist=False        
        try:
            os.rename(file, file + ".bak")
            r = open(file + ".bak", 'r')
            w = open(file, 'w')
            for line in r:
                if re.search(searchExp, line):
                    line = re.sub(searchExp, replaceExp, line)
                    exist=True
                w.write(line)
            if exist == False:
                w.write(replaceExp + "\n")
        finally:
            r.close() 
            w.close() 
            os.remove(file + ".bak")
    else:
        print file + " doesn't exist"
    
###

def disable_service(name):
    '''Disable autostartup of a service and stop the service'''
    process = subprocess.Popen('chkconfig --list |grep "3:on" |awk \'{print $1}\' |grep ' + name, shell=True, stdout=subprocess.PIPE)
    if process.communicate()[0][:-1] == name:
        subprocess.call(["chkconfig", name,  "off"])
    
    process = subprocess.Popen('service ' + name + ' status', shell=True, stdout=subprocess.PIPE)
    if 'stopped' not in process.communicate()[0][:-1]:
        subprocess.call(["/sbin/service", name, "stop"])
        
###

def rpm_remove(name):
    '''Remove rpm packages'''
    process = subprocess.Popen('rpm -q ' + name, shell=True, stdout=subprocess.PIPE)
    if process.communicate()[0][:-1] != "package " + name + " is not installed":
        shell_exec("rpm -e " + name)        
        
# Add personal user
#
def user_add():
    print_label('User add')

    name = ""
    while name == "":
        name = raw_input("User name:")

    shell_exec("useradd " + name + " -G wheel,root")
    while shell_exec("passwd " + name):
        pass
        
    shell_exec("chmod +w /etc/sudoers")
    set_config_property("/etc/sudoers",'^# %wheel.*ALL=\(ALL\).*ALL$',"%wheel        ALL=(ALL)       ALL")
    shell_exec("chmod 0440 /etc/sudoers")     
    
    process = subprocess.Popen('visudo -c', shell=True, stdout=subprocess.PIPE)
    if process.communicate()[0][:-1] != "/etc/sudoers: parsed OK":
        print "ERROR: /etc/sudoers is not ok"
        sys.exit()  
        
# Enable selinux
#
# All machines should have selinux on by default.
# For more info: http://www.crypt.gen.nz/selinux/disable_selinux.html
def enable_selinux():
    print_label("Enable SELinux")
    if grep("/etc/selinux/config", "SELINUX=disabled"):
        print "More need to be done, read http://www.crypt.gen.nz/selinux/disable_selinux.html"
    else:
        set_config_property("/etc/selinux/config",'^SELINUX=.*$',"SELINUX=enforcing")
        set_config_property("/etc/selinux/config",'^SELINUXTYPE=.*$',"SELINUXTYPE=targeted")

# Disable services
#
# Turn of autostart of services that are not used, and dont need to be used
# on a default centos server.
#
# Which services are autostarted
# chkconfig  --list |grep on
#
# Which services are autostarted in level 3
# chkconfig --list |grep "3:on" |awk '{print $1}' |sort
#
# What status has the services, started/stopped?
# /sbin/service --status-all
#
# For more info:
# http://www.sonoracomm.com/support/18-support/114-minimal-svcs
# http://www.imminentweb.com/technologies/centos-disable-unneeded-services-boot-time
# http://magazine.redhat.com/2007/03/09/understanding-your-red-hat-enterprise-linux-daemons/
def disable_services():
    print_label("Disable services")
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

# Disable Virtual terminals
#
def disable_virtual_terminals():
    print_label("Disable virtual terminals")
    set_config_property("/etc/inittab", "^[#]?2:2345:respawn:/sbin/mingetty tty2$","#2:2345:respawn:/sbin/mingetty tty2")
    set_config_property("/etc/inittab", "^[#]?3:2345:respawn:/sbin/mingetty tty3$","#3:2345:respawn:/sbin/mingetty tty3")
    set_config_property("/etc/inittab", "^[#]?4:2345:respawn:/sbin/mingetty tty4$","#4:2345:respawn:/sbin/mingetty tty4")
    set_config_property("/etc/inittab", "^[#]?5:2345:respawn:/sbin/mingetty tty5$","#5:2345:respawn:/sbin/mingetty tty5")
    set_config_property("/etc/inittab", "^[#]?6:2345:respawn:/sbin/mingetty tty6$","#6:2345:respawn:/sbin/mingetty tty6")
    
# Disable IP6 support
#
def disable_ip6_support():
    print_label("Disable IP6 support")
    set_config_property("/etc/modprobe.conf", "^alias ipv6 off$","alias ipv6 off")
    set_config_property("/etc/modprobe.conf", "^alias net-pf-10 off$","alias net-pf-10 off")
    set_config_property("/etc/sysconfig/network", "^NETWORKING_IPV6=.*$","NETWORKING_IPV6=no")
    shell_exec("service network restart")

# Remove rpms we are note using
#
def remove_rpms():
    print_label("Remove rpms")
    rpm_remove("unix2dos-2.2-26.2.3.el5")
    rpm_remove("mkbootdisk-1.5.3-2.1.x86_64")
    rpm_remove("dosfstools-2.11-7.el5")
    rpm_remove("dos2unix-3.1-27.2.el5")
    rpm_remove("finger-0.17-32.2.1.1")
    rpm_remove("firstboot-tui-1.4.27.7-1.el5.centos")

# Customize shell
#
def customize_shell():
    print_label("Customize shell")

    print "Add Date And Time To History Output"
    set_config_property("/etc/bashrc", "^export HISTTIMEFORMAT=.*$","export HISTTIMEFORMAT=\"%h/%d - %H:%M:%S \"")
    
    print "Add Color To Grep"
    set_config_property("/root/.bash_profile", "^export GREP_COLOR=.*$","export GREP_COLOR='1;32'")
    set_config_property("/root/.bash_profile", "^export GREP_OPTIONS=.*$","export GREP_OPTIONS=--color=auto")
    set_config_property("/etc/skel/.bash_profile", "^export GREP_COLOR=.*$","export GREP_COLOR='1;32'")
    set_config_property("/etc/skel/.bash_profile", "^export GREP_OPTIONS=.*$","export GREP_OPTIONS=--color=auto")

# Hardening
#
def hardening():
    print_label("Hardening")
    
    print "Disable Usb Drives If Server Is Accessible Or Has Sensitive Data"
    set_config_property("/etc/modprobe.d/blacklist-usbstorage", "^blacklist usb-storage$","blacklist usb-storage")
    
    print "Disallow Root Ssh Login (Must Su To Root)"
    set_config_property("/etc/ssh/sshd_config", "^[#]*PermitRootLogin.*$","PermitRootLogin no")
    
    print "Passwords Should Be Stored In Sha512 Instead Of Md5"
    shell_exec("authconfig --passalgo=sha512 --update")
    
    print "Help kernel to prevent certain kinds of attacks"
    set_config_property("/etc/sysctl.conf", "^net.ipv4.icmp_ignore_bogus_error_messages=.*$","net.ipv4.icmp_ignore_bogus_error_messages=1")
    set_config_property("/etc/sysctl.conf", "^kernel.exec-shield=.*$","kernel.exec-shield=1")
    set_config_property("/etc/sysctl.conf", "^kernel.randomize_va_space=.*$","kernel.randomize_va_space=1")
    set_config_property("/etc/sysctl.conf", "^net.ipv4.icmp_echo_ignore_broadcasts=.*$","net.ipv4.icmp_echo_ignore_broadcasts=1")

# Update
#
def update():
    print_label("Update with yum")
    shell_exec("yum update -y")

# Reboot
#
def reboot():
    print_label("System is going down for reboot")
    shell_exec("reboot")

# The main function
#   
def main():    
    user_add()
    enable_selinux()
    disable_services()
    disable_virtual_terminals()
    disable_ip6_support()
    remove_rpms()
    customize_shell()
    hardening()
    update()   
#    reboot()

# Call the main function
#
main()[root@fo-tp-vh01 ~]# 
