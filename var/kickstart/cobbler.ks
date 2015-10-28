# SYCO kickstart for cobbler installed hosts/guests.
#
# Author: Daniel Lindh <daniel@cybercow.se>
#
# On kvm host run
# cobbler profile getks --name=centos-vm_guest
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

# Use network installation
url --url=$tree

# If any cobbler repo definitions were referenced in the kickstart profile, include them here.
$yum_repo_stanza

# Network information
$SNIPPET('network_config')

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
# See installCobbler.py when changing disk usage.
#
clearpart --all --drives=$boot_device --initlabel
part /boot --fstype ext4 --size=200 --ondisk=$boot_device
part pv.2 --size=$total_disk_mb --grow --ondisk=$boot_device
volgroup $vol_group pv.2
logvol swap           --fstype swap --name=swap        --vgname=$vol_group --size=$disk_swap_mb
logvol /              --fstype ext4 --name=root        --vgname=$vol_group --size=4096
logvol /var           --fstype ext4 --name=var         --vgname=$vol_group --size=$disk_var_mb
logvol /home          --fstype ext4 --name=home        --vgname=$vol_group --size=1024 --fsoptions=noexec,nodev,nosuid
logvol /var/tmp       --fstype ext4 --name=vartmp      --vgname=$vol_group --size=1024 --fsoptions=noexec,nodev,nosuid
logvol /var/log       --fstype ext4 --name=varlog      --vgname=$vol_group --size=$disk_log_mb --fsoptions=noexec,nodev,nosuid
logvol /var/log/audit --fstype ext4 --name=varlogaudit --vgname=$vol_group --size=1024 --fsoptions=noexec,nodev,nosuid
logvol /tmp           --fstype ext4 --name=tmp         --vgname=$vol_group --size=1024 --fsoptions=noexec,nodev,nosuid

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

%pre
$SNIPPET('log_ks_pre')
$SNIPPET('kickstart_start')
$SNIPPET('pre_install_network_config')
# Enable installation monitoring
$SNIPPET('pre_anamon')
%end

%post
$SNIPPET('log_ks_post')
# Start yum configuration
$yum_config_stanza
# End yum configuration
$SNIPPET('post_install_kernel_options')
$SNIPPET('post_install_network_config')
$SNIPPET('func_register_if_enabled')
$SNIPPET('download_config_files')
$SNIPPET('koan_environment')
$SNIPPET('redhat_register')
$SNIPPET('cobbler_register')
# Enable post-install boot notification
$SNIPPET('post_anamon')
# Start final steps
$SNIPPET('kickstart_done')
# End final steps
%end
