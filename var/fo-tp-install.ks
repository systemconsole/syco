# Fareoffice fo-tp-install kickstart.
# Author: Daniel Lindh
# Created: 2010-11-29
#
# This file is not used with cobbler.
#
# Documentation
# http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/ch-kickstart2.html
# http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html

# System authorization information
auth  --useshadow  --enablemd5

# Bootloader
# disable usb as per NSA 2.2.2.2.3:
bootloader --location=mbr --append="rhgb quiet nousb" --driveorder=vda


# Clear the Master Boot Record
zerombr

# Use text mode install
text

# Firewall configuration
firewall --enabled --port=22:tcp

# Run the Setup Agent on first boot
firstboot --disable

# System keyboard
keyboard sv-latin1

# System language
lang en_US.UTF-8

# Network information
# Using "old" style networking config. Make sure all MAC-addresses are in cobbler to use the new-style config
network --bootproto=static --ip=10.100.100.200 --netmask=255.255.0.0 --gateway=10.100.0.1 --hostname=fo-tp-install --device=eth0 --onboot=on --nameserver 10.100.0.4 

# Reboot after installation
reboot

#Root password
rootpw --iscrypted $1$vfg34t55$JsSc9Us8Aje0auu.4ZnHn1

# SELinux configuration
selinux --enforcing

# Do not configure the X Window System
skipx

# System timezone
timezone --utc Europe/Stockholm

# Install OS instead of upgrade
install

# Partioning
clearpart --all --drives=vda --initlabel
part /boot --fstype ext3 --size=100 --ondisk=vda
part pv.2 --size=0 --grow --ondisk=vda
volgroup VolGroup00 pv.2

logvol swap     --fstype swap --name=swap   --vgname=VolGroup00 --size=4096
logvol /        --fstype ext3 --name=root   --vgname=VolGroup00 --size=4096
logvol /var     --fstype ext3 --name=var    --vgname=VolGroup00 --size=32768
logvol /var/tmp --fstype ext3 --name=vartmp --vgname=VolGroup00 --size=1024 --fsoptions=noexec, nosuid, nodev
logvol /var/log --fstype ext3 --name=varlog --vgname=VolGroup00 --size=4096 --fsoptions=noexec, nosuid, nodev
logvol /tmp     --fstype ext3 --name=tmp    --vgname=VolGroup00 --size=1024 --fsoptions=noexec, nosuid, nodev
logvol /home    --fstype ext3 --name=home   --vgname=VolGroup00 --size=1024 --fsoptions=noexec, nosuid, nodev

%packages
@base
@core
keyutils
trousers
fipscheck
device-mapper-multipath
python26
python-paramiko
git

%post
rpm -Uhv http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm
yum -y install python-paramiko