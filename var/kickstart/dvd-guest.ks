# SYCO kickstart for guest hosts installation with dvd (not with cobbler).
#
# Author: Daniel Lindh <daniel@cybercow.se>
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
authconfig --enableshadow  --enablemd5

# Bootloader
# Put a password on the boot loader to keep the riff raff out,
bootloader --location=mbr --append="rhgb quiet" --driveorder=$boot_device --md5pass="$default_password_crypted"

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
network --bootproto=static --ip=$back_ip  --netmask=$back_netmask  --gateway=$back_gateway  --hostname=$hostname --device=eth0 --onboot=on --nameserver=$back_nameserver  --noipv6
network --bootproto=static --ip=$front_ip --netmask=$front_netmask --gateway=$front_gateway --hostname=$hostname --device=eth1 --onboot=on --nameserver=$front_nameserver --noipv6

# Reboot after installation
reboot

#Root password
rootpw --iscrypted "$default_password_crypted"

# SELinux configuration
selinux --enforcing

# Do not configure the X Window System
skipx

# System timezone
timezone --utc Europe/Stockholm

# Install OS instead of upgrade
install

# Partioning
#
# See installGuestWithDVD.py when changing disk usage.
#
clearpart --all --drives=$boot_device --initlabel
part /boot --fstype ext4 --size=100 --ondisk=$boot_device
part pv.2 --size=$total_disk_mb --grow --ondisk=$boot_device
volgroup VolGroup00 pv.2
logvol swap           --fstype swap --name=lv_swap        --vgname=VolGroup00 --size=$disk_swap_mb
logvol /              --fstype ext4 --name=lv_root        --vgname=VolGroup00 --size=4096
logvol /var           --fstype ext4 --name=lv_var         --vgname=VolGroup00 --size=$disk_var_mb
logvol /home          --fstype ext4 --name=lv_home        --vgname=VolGroup00 --size=1024 --fsoptions=noexec,nodev,nosuid
logvol /var/tmp       --fstype ext4 --name=lv_vartmp      --vgname=VolGroup00 --size=1024 --fsoptions=noexec,nodev,nosuid
logvol /var/log       --fstype ext4 --name=lv_varlog      --vgname=VolGroup00 --size=$disk_log_mb --fsoptions=noexec,nodev,nosuid
logvol /var/log/audit --fstype ext4 --name=lv_varlogaudit --vgname=VolGroup00 --size=1024 --fsoptions=noexec,nodev,nosuid
logvol /tmp           --fstype ext4 --name=lv_tmp         --vgname=VolGroup00 --size=1024 --fsoptions=noexec,nodev,nosuid

services --disabled=smartd --enabled=acpid

# Followig is MINIMAL https://partner-bugzilla.redhat.com/show_bug.cgi?id=593309
# Also have a look in hardening/package.py
%packages --nobase
@server-policy

# Enables shutdown etc. from virsh
acpid

coreutils
cronie-anacron
e2fsprogs
git
grub
lvm2
man
mlocate
nspr
nss
nss-util
openssh
openssh-clients
openssh-server
policycoreutils-python
rpm
wget
yum
yum-presto
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
-rt61pci-firmware
-rt73usb-firmware
-xorg-x11-drv-ati-firmware
-zd1211-firmware
%end
