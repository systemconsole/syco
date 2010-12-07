# Fareoffice default kickstart file
#
# Author: Daniel Lindh
# Created: 2010-11-10
#
# On kvm host run
# cobbler profile getks --name=centos5.5-vm_guest
#
# Documentation
# http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/ch-kickstart2.html
# http://docs.redhat.com/docs/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s1-kickstart2-options.html

# System authorization information
auth  --useshadow  --enablemd5

# Logging
# One of debug, info, warning, error, or critical.
#logging --host=10.100.100.200 --port=XX --level=debug

# System bootloader configuration
bootloader --location=mbr --driveorder=hda --md5pass="$default_password_crypted"

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
rootpw --iscrypted $default_password_crypted

# SELinux configuration
selinux --enforcing

# Do not configure the X Window System
skipx

# System timezone
timezone --utc Europe/Stockholm

# Install OS instead of upgrade
install

# Partioning
clearpart --all --drives=hda --initlabel
part /boot --fstype ext3 --size=100 --ondisk=hda
part pv.2 --size=0 --grow --ondisk=hda
volgroup VolGroup00 pv.2
logvol /home --fstype ext3 --name=home --vgname=VolGroup00 --size=1024
logvol /var     --fstype ext3 --name=var    --vgname=VolGroup00 --size=32768
logvol /var/tmp --fstype ext3 --name=vartmp --vgname=VolGroup00 --size=1024
logvol /var/log --fstype ext3 --name=varlog --vgname=VolGroup00 --size=4096
logvol /tmp --fstype ext3 --name=tmp --vgname=VolGroup00 --size=1024
logvol / --fstype ext3 --name=root --vgname=VolGroup00 --size=4096
logvol swap --fstype swap --name=swap --vgname=VolGroup00 --size=4096

#services --disabled=xxx,yyy

%packages
@base
@core
keyutils
trousers
fipscheck
device-mapper-multipath
#python-paramiko
#-autofs

%pre
$SNIPPET('log_ks_pre')
$kickstart_start
$SNIPPET('pre_install_network_config')
# Enable installation monitoring
$SNIPPET('pre_anamon')

%packages
$SNIPPET('func_install_if_enabled')

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
$kickstart_done
# End final steps
rpm -Uhv http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm
yum -y install python-paramiko