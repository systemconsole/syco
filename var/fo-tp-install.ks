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

# System bootloader configuration
bootloader --location=mbr --driveorder=hda

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
url --url=http://ftp.sunet.se/pub/Linux/distributions/centos/5.5/os/x86_64/

# If any cobbler repo definitions were referenced in the kickstart profile, include them here.
repo --name=centos5-updates-x86_64 --baseurl=http://10.100.100.200/cobbler/repo_mirror/centos5-updates-x86_64
repo --name=source-1 --baseurl=http://10.100.100.200/cobbler/ks_mirror/centos5.5-x86_64

# Network information
# Using "old" style networking config. Make sure all MAC-addresses are in cobbler to use the new-style config
network --bootproto=static --ip=10.100.100.200 --netmask=255.255.0.0 --gateway=10.100.0.1 --hostname=fo-tp-svn --device=eth0 --onboot=on

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
clearpart --all --drives=hda --initlabel
part /boot --fstype ext3 --size=100 --ondisk=hda
part pv.2 --size=0 --grow --ondisk=hda
volgroup VolGroup00 pv.2
logvol /home    --fstype ext3 --name=home   --vgname=VolGroup00 --size=1024
logvol /var/tmp --fstype ext3 --name=vartmp --vgname=VolGroup00 --size=1024
logvol /var/log --fstype ext3 --name=varlog --vgname=VolGroup00 --size=4096
logvol /tmp     --fstype ext3 --name=tmp    --vgname=VolGroup00 --size=1024
logvol /        --fstype ext3 --name=root   --vgname=VolGroup00 --size=4096
logvol /opt     --fstype ext3 --name=data   --vgname=VolGroup00 --size=4096
logvol swap     --fstype swap --name=swap   --vgname=VolGroup00 --size=4096

%packages
@base
@core
keyutils
trousers
fipscheck
device-mapper-multipath

%pre
set -x -v
exec 1>/tmp/ks-pre.log 2>&1

# Once root's homedir is there, copy over the log.
while : ; do
    sleep 10
    if [ -d /mnt/sysimage/root ]; then
        cp /tmp/ks-pre.log /mnt/sysimage/root/
        logger "Copied %pre section log to system"
        break
    fi
done &


%packages

%post
set -x -v
exec 1>/root/ks-post.log 2>&1

# End yum configuration


# Start post_install_network_config generated code
mkdir /etc/sysconfig/network-scripts/cobbler
cp /etc/sysconfig/network-scripts/ifcfg-lo /etc/sysconfig/network-scripts/cobbler/
grep -v GATEWAY /etc/sysconfig/network > /etc/sysconfig/network.cobbler
echo "GATEWAY=10.100.0.1" >> /etc/sysconfig/network.cobbler
grep -v HOSTNAME /etc/sysconfig/network > /etc/sysconfig/network.cobbler
echo "HOSTNAME=fo-tp-svn" >> /etc/sysconfig/network.cobbler
rm -f /etc/sysconfig/network
mv /etc/sysconfig/network.cobbler /etc/sysconfig/network
/bin/hostname fo-tp-svn

# Start configuration for eth0
MAC=$(ifconfig -a | grep eth0 | awk '{ print $5 }')
echo "DEVICE=eth0" > /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
echo "HWADDR=$MAC" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
echo "ONBOOT=yes" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
echo "BOOTPROTO=static" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
echo "IPADDR=10.100.100.200" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
echo "NETMASK=255.255.0.0" >> /etc/sysconfig/network-scripts/cobbler/ifcfg-eth0
# End configuration for eth0

rm -f /etc/sysconfig/network-scripts/ifcfg-*
mv /etc/sysconfig/network-scripts/cobbler/* /etc/sysconfig/network-scripts/
rm -r /etc/sysconfig/network-scripts/cobbler
if [ -f "/etc/modprobe.conf" ]; then
cat /etc/modprobe.conf.cobbler >> /etc/modprobe.conf
rm -f /etc/modprobe.conf.cobbler
fi
# End post_install_network_config generated code