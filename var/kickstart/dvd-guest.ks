# SYCO kickstart for guest hosts installation with dvd (not with cobbler).
#
# Author: Daniel Lindh <daniel@cybercow.se>
# Created: 2010-11-29
#
# Documentation
# http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/ch-kickstart2.html
# http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html
# http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-packageselection.html
# http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-startinginstall.html

# Logging
# One of debug, info, warning, error, or critical.
#logging --host=10.100.100.200 --port=XX --level=debug

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
network --bootproto=static --ip=${BACK_IP}  --netmask=${BACK_NETMASK}  --gateway=${BACK_GATEWAY}  --hostname=${HOSTNAME} --device=eth0 --onboot=on --nameserver=${BACK_NAMESERVER}  --noipv6
network --bootproto=static --ip=${FRONT_IP} --netmask=${FRONT_NETMASK} --gateway=${FRONT_GATEWAY} --hostname=${HOSTNAME} --device=eth1 --onboot=on --nameserver=${FRONT_NAMESERVER} --noipv6

# Reboot after installation
reboot

#Root password
rootpw --iscrypted ${ROOT_PASSWORD}

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
part /boot --fstype ext4 --size=100 --ondisk=vda
part pv.2 --size=${TOTAL_DISK_MB} --grow --ondisk=vda
volgroup VolGroup00 pv.2
logvol swap     --fstype swap --name=swap   --vgname=VolGroup00 --size=4096
logvol /        --fstype ext4 --name=root   --vgname=VolGroup00 --size=4096
logvol /var     --fstype ext4 --name=var    --vgname=VolGroup00 --size=${DISK_VAR_MB}
logvol /home    --fstype ext4 --name=home   --vgname=VolGroup00 --size=1024 --fsoptions=noexec, nosuid, nodev
logvol /var/tmp --fstype ext4 --name=vartmp --vgname=VolGroup00 --size=1024 --fsoptions=noexec, nosuid, nodev
logvol /var/log --fstype ext4 --name=varlog --vgname=VolGroup00 --size=4096 --fsoptions=noexec, nosuid, nodev
logvol /tmp     --fstype ext4 --name=tmp    --vgname=VolGroup00 --size=1024 --fsoptions=noexec, nosuid, nodev

services --disabled=smartd --enabled=acpid

# Followig is MINIMAL https://partner-bugzilla.redhat.com/show_bug.cgi?id=593309
%packages --nobase
# @core
@server-policy
policycoreutils-python

# Enables shutdown etc. from virsh
acpid

git
coreutils
yum
rpm
e2fsprogs
lvm2
grub
openssh-server
openssh-clients
yum-presto
man
mlocate
wget
-atmel-firmware
-b43-openfwwf
-ipw2100-firmware
-ipw2200-firmware
-ivtv-firmware
-iwl1000-firmware
-iwl3945-firmware
-iwl4965-firmware
-iwl5000-firmware
-iwl5150-firmware
-iwl6000-firmware
-iwl6050-firmware
-libertas-usb8388-firmware
-zd1211-firmware
-xorg-x11-drv-ati-firmware
