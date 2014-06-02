#!/bin/sh
#
# firewall.sh - Firewall script for the office at Telefonplan
#
# Copyright (C) 2011, The System Console project"

# Author daniel.lindh@cybercow.se
#
# More documentation about the telefonplan network can be found at
# https://redmine.fareoffice.com/projects/sysops/wiki/TelefonplanNetworkSchema
# https://redmine.fareoffice.com/projects/sysops/wiki/Fo-tp-fw
#
# This script is based on Oskar Andreassons rc.DMZ.firewall.txt
# Read and learn more about iptables.
# http://www.frozentux.net/iptables-tutorial/scripts/rc.DMZ.firewall.txt
# http://www.frozentux.net/iptables-tutorial/iptables-tutorial.html
# http://manpages.ubuntu.com/manpages/jaunty/man8/iptables.8.html
# http://www.cipherdyne.org/psad/
#
#
# TODO:
# * Add recent http://www.snowman.net/projects/ipt_recent/
#   http://www.frozentux.net/iptables-tutorial/scripts/recent-match.txt
# * SSH till burken får bara göras ifrån vissa ip??
###########################################################################

#
# Configuration options.
#

# External DNS server to user. Using ownit and google dns.
DNS_SERVER="84.246.88.10 84.246.88.20 8.8.8.8 83.140.64.189"

# Our secondary DNS on internet (not used by LAN USER)
DNS2_IP="8.8.8.8"

# Internet Configuration.
INET_IP="178.78.197.210"
PHPHTTP_IP="178.78.197.210"
MAIL_IP="178.78.197.211"
DNS_IP="178.78.197.212"
VPN_IP="178.78.197.210"
FILE_IP="178.78.197.210"
PHONE_IP="178.78.197.210"
FP_UAT_IP="31.211.193.10"
FO_UAT_IP="31.211.193.11"
VCS_IP="178.78.197.212"
REDMINE_IP="31.211.193.14"
FO_PROD_IP="178.78.197.213"
INET_IFACE="eth3"

# 31.211.193.12 - Used by pfsense
# 31.211.193.13 - Free to use.
# 178.78.197.214 - Might be free to use

# Local Area Network configuration.
LAN_IP="192.168.0.1"
LAN_IFACE="eth2"

# DMZ Configuration.
DMZ_IP="10.100.0.1"
DMZ_MAIL_IP="10.100.131.21"
DMZ_DNS_IP="10.100.0.10"
DMZ_VPN_IP="10.100.131.10"
DMZ_FILE_IP="10.100.131.20"
DMZ_PHONE_IP="10.100.0.3"
DMZ_PHPHTTP_IP="10.100.0.4"
DMZ_FP_UAT_IP="10.100.131.122"
DMZ_FO_UAT_IP="10.100.131.112"
DMZ_VCS_IP="10.100.131.22"
DMZ_REDMINE_IP="10.100.111.30"
DMZ_FO_PROD_IP="10.100.111.115"
DMZ_IFACE="eth0"

# Localhost Configuration.
LO_IFACE="lo"
LO_IP="127.0.0.1"

# Wireless Configuration.
WIRELESS_IP="192.168.1.1"
WIRELESS_IFACE="eth1"

# DHCP

# IPTables Configuration.
IPTABLES="/sbin/iptables"
USAGE="$0 [--log | --accept] [on | off | save]"

###########################################################################
#
# FUNCTIONS
#

#############################################
# Module loading.s
#############################################

function firewall_on {

###########################################################################
#
# Setup ip forwarding
#
echo "1" > /proc/sys/net/ipv4/ip_forward

###########################################################################
#
# Setup rules
#

# Set policies
$IPTABLES -P INPUT DROP
$IPTABLES -P OUTPUT DROP
$IPTABLES -P FORWARD DROP

# Create bad_tcp_packets chain
$IPTABLES -N bad_tcp_packets
$IPTABLES -A bad_tcp_packets -p tcp --tcp-flags SYN,ACK SYN,ACK -m state --state NEW -j REJECT --reject-with tcp-reset
# Generates to much logs $IPTABLES -A bad_tcp_packets -p tcp ! --syn -m state --state NEW -j LOG --log-prefix "New not syn:"
$IPTABLES -A bad_tcp_packets -p tcp ! --syn -m state --state NEW -j DROP

# Create allowed chain
$IPTABLES -N allowed
$IPTABLES -A allowed -p TCP --syn -j ACCEPT
$IPTABLES -A allowed -p TCP -m state --state ESTABLISHED,RELATED -j ACCEPT
$IPTABLES -A allowed -p TCP -j DROP

# Create ICMP rules
$IPTABLES -N icmp_packets
$IPTABLES -A icmp_packets -p ICMP -s 0/0 --icmp-type echo-request -j ACCEPT
$IPTABLES -A icmp_packets -p ICMP -s 0/0 --icmp-type echo-reply -j ACCEPT
$IPTABLES -A icmp_packets -p ICMP -s 0/0 --icmp-type destination-unreachable -j ACCEPT
$IPTABLES -A icmp_packets -p ICMP -s 0/0 --icmp-type source-quench -j ACCEPT
$IPTABLES -A icmp_packets -p ICMP -s 0/0 --icmp-type time-exceeded -j ACCEPT
$IPTABLES -A icmp_packets -p ICMP -s 0/0 --icmp-type parameter-problem -j ACCEPT

###########################################################################
#
# General rules
#

# Bad TCP packets we don't want
$IPTABLES -A INPUT   -p tcp -j bad_tcp_packets
$IPTABLES -A OUTPUT  -p tcp -j bad_tcp_packets
$IPTABLES -A FORWARD -p tcp -j bad_tcp_packets

# Standard icmp_packets from anywhere
$IPTABLES -A INPUT  -p ICMP -j icmp_packets
$IPTABLES -A OUTPUT -p ICMP -j icmp_packets

allow_fw_to_access_external_dns



###########################################################################
#
# INPUT chain
#

#
# From anywhere
#

# SSH open from anywhere
#$IPTABLES -A INPUT -p TCP --sport 1024:65535 --dport 34 -j allowed
$IPTABLES -A INPUT -p TCP --dport 34 -j allowed
$IPTABLES -A INPUT -p TCP --dport 5666 -j allowed


# Didn't get it to work
# $IPTABLES -A INPUT -p TCP --dport 34 -m state --state NEW -m recent --name sshprobe --set -j allowed
# $IPTABLES -A INPUT -p TCP --dport 34 -m state --state NEW -m recent --name sshprobe --update --seconds 60 --hitcount 3 --rttl -j DROP

#
# From the Internet to INET firewall IP
#

#
# From DMZ Interface to DMZ firewall IP
#

#
# From LAN Interface to LAN firewall IP
#

# Special rule for DHCP requests from LAN, which are not caught properly
# otherwise.
$IPTABLES -A INPUT -p UDP -i $LAN_IFACE --dport 67:68 --sport 67:68 -j ACCEPT
$IPTABLES -A OUTPUT -p UDP  --dport 67:68 --sport 67:68 -j ACCEPT

#
# From WIRELESS Interface to WIRELESS firewall IP
#

# From Localhost interface to Localhost IP's
$IPTABLES -A INPUT -p ALL -i $LO_IFACE -s $LO_IP -j ACCEPT
$IPTABLES -A INPUT -p ALL -i $LO_IFACE -s $LAN_IP -j ACCEPT
$IPTABLES -A INPUT -p ALL -i $LO_IFACE -s $INET_IP -j ACCEPT


###########################################################################
#
# OUTPUT chain
#

# Firewall can SSH to any other computer internal and external.
$IPTABLES -A OUTPUT -p tcp -m multiport --dports 22,34 -j ACCEPT

# Allow yum updates through http
$IPTABLES -A OUTPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

###########################################################################
#
# FORWARD chain
#

# Lan can access dns on internet.
allow_clients_to_access_external_dns

# internet/lan/wireless can access DNS in DMZ.
forward_to_internal_dns

# DMZ are allowed to access internet
$IPTABLES -A FORWARD -i $DMZ_IFACE -o $INET_IFACE -j ACCEPT

# DMZ are allowed to access DMZ
$IPTABLES -A FORWARD -i $DMZ_IFACE -o $DMZ_IFACE -j ACCEPT

# DMZ are allowed to access LAN
$IPTABLES -A FORWARD -i $DMZ_IFACE -o $LAN_IFACE -j ACCEPT

# LAN are allowed to access DMZ
$IPTABLES -A FORWARD -i $LAN_IFACE -o $DMZ_IFACE -j ACCEPT

# LAN are allowed to access INET
$IPTABLES -A FORWARD -i $LAN_IFACE -o $INET_IFACE -j ACCEPT

# LAN are allowed to access LAN
$IPTABLES -A FORWARD -i $LAN_IFACE -o $LAN_IFACE -j ACCEPT

# LAN are allowed to access internet
# 8000,8001=radiostream
$IPTABLES -A FORWARD -p TCP -i $LAN_IFACE  -o $INET_IFACE -m multiport --dports 22,25,30,80,443,8000,8001,8080,7080,3306,53 -j allowed
$IPTABLES -A FORWARD -p ICMP -i $LAN_IFACE -o $INET_IFACE -j icmp_packets

# LAN are allowed to access external mail servers
$IPTABLES -A FORWARD -p TCP -i $LAN_IFACE -o $INET_IFACE -d smtp.gmail.com -m multiport --dports 25                  -j allowed
$IPTABLES -A FORWARD -p TCP -i $LAN_IFACE -o $INET_IFACE -d imap.gmail.com -m multiport --dports 143                 -j allowed
$IPTABLES -A FORWARD -p TCP -i $LAN_IFACE -o $INET_IFACE -d mail.mac.com   -m multiport --dports 25,143,110,993,5087 -j allowed
$IPTABLES -A FORWARD -p TCP -i $LAN_IFACE -o $INET_IFACE -d mail.me.com    -m multiport --dports 25,143,110,993,5087 -j allowed

# Everybody are allowd to access Netgiro servers
$IPTABLES -A FORWARD -p TCP -o $INET_IFACE -d 195.149.170.66 -j allowed

# Everybody are allowd to access Enterprise servers
$IPTABLES -A FORWARD -p TCP -o $INET_IFACE -d vanguardcar.com -j allowed
$IPTABLES -A FORWARD -p TCP -o $INET_IFACE -d www.vanguardcar.com -j allowed
$IPTABLES -A FORWARD -p TCP -o $INET_IFACE -d uat.vanguardcar.com -j allowed
$IPTABLES -A FORWARD -p TCP -o $INET_IFACE -d mo.vanguardcar.com -j allowed

# Everybody are allowd to whois servers
$IPTABLES -A FORWARD -p TCP -o $INET_IFACE -d whois.nic-se.se --dport 43 -j allowed
$IPTABLES -A FORWARD -p TCP -o $INET_IFACE -d whois.ripe.net --dport 43 -j allowed

# Everybody are allowed to use NTP servers.
$IPTABLES -A FORWARD -p UDP -o $INET_IFACE -d ntp1.sp.se --dport 123 -j ACCEPT

# DMZ to servers that need survaliance (nagios, munin)
$IPTABLES -A FORWARD -p TCP -i $DMZ_IFACE -o $INET_IFACE -d 88.80.165.132 -m multiport --dports 5666,4949 -j allowed
$IPTABLES -A FORWARD -p TCP -i $DMZ_IFACE -o $INET_IFACE -d 88.80.165.134 -m multiport --dports 5666,4949 -j allowed
$IPTABLES -A FORWARD -p TCP -i $DMZ_IFACE -o $INET_IFACE -d 81.201.214.10 -m multiport --dports 5666,4949 -j allowed
$IPTABLES -A FORWARD -p TCP -i $DMZ_IFACE -o $INET_IFACE -d 81.201.214.12 -m multiport --dports 5666,4949 -j allowed

# DMZ HTTP server
$IPTABLES -t nat -A PREROUTING -p TCP -d $PHPHTTP_IP -m multiport --dports 80,443 -j DNAT --to-destination $DMZ_PHPHTTP_IP
$IPTABLES -A FORWARD -p TCP -o $DMZ_IFACE -d $DMZ_PHPHTTP_IP -m multiport --dports 80,443 -j allowed
$IPTABLES -A FORWARD -p ICMP -o $DMZ_IFACE -d $DMZ_PHPHTTP_IP -j icmp_packets

# DMZ Mail server
$IPTABLES -t nat -A PREROUTING -p TCP -d $MAIL_IP -m multiport --dports 7025,25,110,143,80,443,993,995 -j DNAT --to-destination $DMZ_MAIL_IP
$IPTABLES -t nat -A PREROUTING -p TCP -d $MAIL_IP --dport 82 -j DNAT --to-destination $DMZ_MAIL_IP:80
$IPTABLES -t nat -A PREROUTING -p TCP -d $MAIL_IP --dport 445 -j DNAT --to-destination $DMZ_MAIL_IP:443
$IPTABLES -t nat -A PREROUTING -p TCP -d $MAIL_IP --dport 35 -j DNAT --to-destination $DMZ_MAIL_IP:22
$IPTABLES -t nat -A PREROUTING -p TCP -d $MAIL_IP --dport 8025 -j DNAT --to-destination $DMZ_MAIL_IP:25
$IPTABLES -A FORWARD -p TCP  -o $DMZ_IFACE -d $DMZ_MAIL_IP -m multiport --dports 7025,25,110,143,80,443,993,995,22,35 -j allowed
$IPTABLES -A FORWARD -p ICMP -o $DMZ_IFACE -d $DMZ_MAIL_IP -j icmp_packets

#DMZ PHONE
#$IPTABLES -t nat -A PREROUTING -p TCP -d $PHONE_IP --dport 5060 -j DNAT --to-destination $DMZ_PHONE_IP
#$IPTABLES -t nat -A PREROUTING -p UDP -d $PHONE_IP --dport 5060:5082 -j DNAT --to-destination $DMZ_PHONE_IP
#$IPTABLES -t nat -A PREROUTING -p UDP -d $PHONE_IP --dport 10000:20000 -j DNAT --to-destination $DMZ_PHONE_IP
#$IPTABLES -A FORWARD -p TCP  -o $DMZ_IFACE -d $DMZ_PHONE_IP   --dport 5060 -j allowed
#$IPTABLES -A FORWARD -p UDP  -o $DMZ_IFACE -d $DMZ_PHONE_IP   --dport 5060:5082 -j ACCEPT
#$IPTABLES -A FORWARD -p UDP  -o $DMZ_IFACE -d $DMZ_PHONE_IP   --dport 10000:20000 -j ACCEPT

# DMZ VPN
$IPTABLES -t nat -A PREROUTING -p TCP -i $INET_IFACE -d $VPN_IP -m multiport --dports 1194 -j DNAT --to-destination $DMZ_VPN_IP
$IPTABLES -t nat -A PREROUTING -p UDP -i $INET_IFACE -d $VPN_IP -m multiport --dports 1194 -j DNAT --to-destination $DMZ_VPN_IP
$IPTABLES -A FORWARD -p TCP  -o $DMZ_IFACE -d $DMZ_VPN_IP -m multiport --dports 1194 -j allowed
$IPTABLES -A FORWARD -p UDP  -o $DMZ_IFACE -d $DMZ_VPN_IP -m multiport --dports 1194 -j ACCEPT
$IPTABLES -A FORWARD -p ICMP -o $DMZ_IFACE -d $DMZ_VPN_IP -j icmp_packets

$IPTABLES -t nat -A PREROUTING -p TCP -d $VPN_IP --dport 36 -j DNAT --to-destination $DMZ_VPN_IP:22
$IPTABLES -A FORWARD -p TCP -o $DMZ_IFACE -d $DMZ_VPN_IP -m multiport --dports 22,36 -j allowed

# File server
$IPTABLES -t nat -A PREROUTING -p TCP -d $FILE_IP --dport 8022 -j DNAT --to-destination $DMZ_FILE_IP:22
$IPTABLES -A FORWARD -p TCP -o $DMZ_IFACE -d $DMZ_FILE_IP -m multiport --dports 22 -j allowed


#$IPTABLES -t nat -A PREROUTING -p UDP -o $INET_IFACE -d $PHONE_IP -m multiport --dports 5060:5082,10000:20000 -j DNAT --to-destination $DMZ_PHONE_IP
#$IPTABLES -A FORWARD -p UDP  -i $DMZ_IFACE -m multiport --sports 5060:5082,10000:20000 -j ACCEPT

#$IPTABLES -t nat -A PREROUTING -p UDP -i $INET_IFACE -d $PHONE_IP -m multiport --dports 5060 -j DNAT --to-destination $DMZ_PHONE_IP
#$IPTABLES -A FORWARD -p UDP  -o $DMZ_IFACE -d $DMZ_PHONE_IP -m multiport --dports 5060 -j ACCEPT

# Vcs server
$IPTABLES -t nat -A PREROUTING -p TCP -d $VCS_IP -m multiport --dports 22,80,443 -j DNAT --to-destination $DMZ_VCS_IP
$IPTABLES -A FORWARD -p TCP  -o $DMZ_IFACE -d $DMZ_VCS_IP -m multiport --dports 22,80,443 -j allowed

# FO-TC-REDMINE - temporary on the office.
$IPTABLES -t nat -A PREROUTING -p TCP -d $REDMINE_IP -m multiport --dports 80,443 -j DNAT --to-destination $DMZ_REDMINE_IP
$IPTABLES -A FORWARD -p TCP  -o $DMZ_IFACE -d $DMZ_REDMINE_IP -m multiport --dports 80,443 -j allowed

# *-uat-tp.farepayment.com
$IPTABLES -t nat -A PREROUTING -p TCP -d $FP_UAT_IP -m multiport --dports 80,443 -j DNAT --to-destination $DMZ_FP_UAT_IP
$IPTABLES -A FORWARD -p TCP  -o $DMZ_IFACE -d $DMZ_FP_UAT_IP -m multiport --dports 80,443 -j allowed

$IPTABLES -t nat -A PREROUTING -p TCP -i $LAN_IFACE -d $FP_UAT_IP -m multiport --dports 6080,6048,7080,7048 -j DNAT --to-destination $DMZ_FP_UAT_IP
$IPTABLES -A FORWARD -p TCP -i $LAN_IFACE -o $DMZ_IFACE -d $FP_UAT_IP -m multiport --dports 6080,6048,7080,7048 -j allowed

# *-uat-tp.fareoffice.com
$IPTABLES -t nat -A PREROUTING -p TCP -d $FO_UAT_IP -m multiport --dports 80,443 -j DNAT --to-destination $DMZ_FO_UAT_IP
$IPTABLES -A FORWARD -p TCP  -o $DMZ_IFACE -d $DMZ_FO_UAT_IP -m multiport --dports 80,443 -j allowed

$IPTABLES -t nat -A PREROUTING -p TCP -i $LAN_IFACE -d $FO_UAT_IP -m multiport --dports 6080,6048,7080,7048 -j DNAT --to-destination $DMZ_FO_UAT_IP
$IPTABLES -A FORWARD -p TCP -i $LAN_IFACE -o $DMZ_IFACE -d $FO_UAT_IP -m multiport --dports 6080,6048,7080,7048 -j allowed

# *-prod-tp.fareoffice.com
$IPTABLES -t nat -A PREROUTING -p TCP -d $FO_PROD_IP -m multiport --dports 80,443 -j DNAT --to-destination $DMZ_FO_PROD_IP
$IPTABLES -A FORWARD -p TCP  -o $DMZ_IFACE -d $DMZ_FO_PROD_IP -m multiport --dports 80,443 -j allowed

$IPTABLES -t nat -A PREROUTING -p TCP -i $LAN_IFACE -d $FO_PROD_IP -m multiport --dports 6080,6048,7080,7048 -j DNAT --to-destination $DMZ_FO_PROD_IP
$IPTABLES -A FORWARD -p TCP -i $LAN_IFACE -o $DMZ_IFACE -d $FO_PROD_IP -m multiport --dports 6080,6048,7080,7048 -j allowed

###########################################################################
#
# Ending chaings
#

# All established and related packets incoming from anywhere to the
# firewall
$IPTABLES -A INPUT -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT
$IPTABLES -A OUTPUT -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT
$IPTABLES -A FORWARD -p ALL -m state --state ESTABLISHED,RELATED -j ACCEPT

#
# Log weird packets that don't match the above.
#
$IPTABLES -A INPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "IPT INPUT packet died: "
$IPTABLES -A OUTPUT -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "IPT OUTPUT packet died: "
$IPTABLES -A FORWARD -m limit --limit 3/minute --limit-burst 3 -j LOG --log-level DEBUG --log-prefix "IPT FORWARD packet died: "

###########################################################################
#
# POSTROUTING
#

# Internal clients/servers can access the mail server through it's external ip.
#$IPTABLES -t nat -A POSTROUTING -d $DMZ_MAIL_IP -j SNAT --to-source $INET_IP
$IPTABLES -t nat -A POSTROUTING -s 10.100.100.1/255.255.0.0 -d $DMZ_MAIL_IP -j SNAT --to-source $MAIL_IP
$IPTABLES -t nat -A POSTROUTING -s $DMZ_MAIL_IP -o $INET_IFACE -j SNAT --to-source $MAIL_IP

# Enable simple IP Forwarding and Network Address Translation
$IPTABLES -t nat -A POSTROUTING -o $INET_IFACE -j SNAT --to-source $INET_IP
$IPTABLES -t nat -A POSTROUTING -s 10.100.100.1/255.255.0.0 -o $DMZ_IFACE -j SNAT --to-source $INET_IP

}

#############################################
# Allow the firewall server to connect to external DNS
#############################################

function allow_fw_to_access_external_dns {

for ip in $DNS_SERVER
do
	$IPTABLES -A OUTPUT -p udp -s $INET_IP --sport 1024:65535 -d $ip --dport 53 -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A INPUT  -p udp -s $ip --sport 53 -d $INET_IP --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT
	$IPTABLES -A OUTPUT -p tcp -s $INET_IP --sport 1024:65535 -d $ip --dport 53 -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A INPUT  -p tcp -s $ip --sport 53 -d $INET_IP --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT
done

}

#############################################
# Allow the firewall server to connect to external DNS
#############################################

function allow_clients_to_access_external_dns {

for ip in $DNS_SERVER
do
	$IPTABLES -A FORWARD -p udp -i $LAN_IFACE --sport 1024:65535 -d $ip --dport 53 -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A FORWARD -p udp -s $ip --sport 53 -o $LAN_IFACE --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT
	$IPTABLES -A FORWARD -p tcp -i $LAN_IFACE --sport 1024:65535 -d $ip --dport 53 -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A FORWARD -p tcp -s $ip --sport 53 -o $LAN_IFACE --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT
done

}

#############################################
# Let users on internet access the DNS server in the DMZ
# Let the DNS server in DMZ connect to secondary DNS on the Internet.
#############################################

function forward_to_internal_dns {

$IPTABLES -A FORWARD -p ICMP -i $INET_IFACE -o $DMZ_IFACE -d $DMZ_DNS_IP -j icmp_packets

$IPTABLES -t nat -A PREROUTING -p TCP -i $INET_IFACE -d $DNS_IP --dport 53 -j DNAT --to-destination $DMZ_DNS_IP
$IPTABLES -t nat -A PREROUTING -p UDP -i $INET_IFACE -d $DNS_IP --dport 53 -j DNAT --to-destination $DMZ_DNS_IP

$IPTABLES -A FORWARD -p udp -o $DMZ_IFACE -s 0/0 --sport 53         -d $DMZ_DNS_IP --dport 53 -m state --state NEW,ESTABLISHED -j ACCEPT
$IPTABLES -A FORWARD -p udp -o $DMZ_IFACE -s 0/0 --sport 1024:65535 -d $DMZ_DNS_IP --dport 53 -m state --state NEW,ESTABLISHED -j ACCEPT
$IPTABLES -A FORWARD -p udp -i $DMZ_IFACE -s $DMZ_DNS_IP --sport 53 -d 0/0 --dport 53         -m state --state ESTABLISHED -j ACCEPT
$IPTABLES -A FORWARD -p udp -i $DMZ_IFACE -s $DMZ_DNS_IP --sport 53 -d 0/0 --dport 1024:65535 -m state --state ESTABLISHED -j ACCEPT

# Secondary DNS
$IPTABLES -A FORWARD -p tcp -o $DMZ_IFACE -s $DNS2_IP --sport 1024:65535 -d $DMZ_DNS_IP --dport 53 -m state --state NEW,ESTABLISHED -j allowed
$IPTABLES -A FORWARD -p tcp -i $DMZ_IFACE -s $DMZ_DNS_IP --sport 53 -d $DMZ_DNS_IP --dport 1024:65535 -m state --state ESTABLISHED -j allowed

}

#############################################
# Flush all chains
#############################################

function reset_chains {

# reset the default policies in the filter table.
$IPTABLES -P INPUT ACCEPT
$IPTABLES -P FORWARD ACCEPT
$IPTABLES -P OUTPUT ACCEPT

# reset the default policies in the nat table.
$IPTABLES -t nat -P PREROUTING ACCEPT
$IPTABLES -t nat -P POSTROUTING ACCEPT
$IPTABLES -t nat -P OUTPUT ACCEPT

# reset the default policies in the mangle table.
$IPTABLES -t mangle -P PREROUTING ACCEPT
$IPTABLES -t mangle -P POSTROUTING ACCEPT
$IPTABLES -t mangle -P INPUT ACCEPT
$IPTABLES -t mangle -P OUTPUT ACCEPT
$IPTABLES -t mangle -P FORWARD ACCEPT

# Flush all chains
$IPTABLES -F -t filter
$IPTABLES -F -t nat
$IPTABLES -F -t mangle

# Delete all user-defined chains
$IPTABLES -X -t filter
$IPTABLES -X -t nat
$IPTABLES -X -t mangle

# Zero all counters
$IPTABLES -Z -t filter
$IPTABLES -Z -t nat
$IPTABLES -Z -t mangle

}

#############################################
# firewall_save
#############################################
#

function firewall_save {

IPTABLES_CONFIG=/etc/sysconfig/iptables

$IPTABLES-save > ${IPTABLES_CONFIG}

}

#############################################
# Module loading.s
#############################################

function load_modules {

/sbin/depmod -a

/sbin/modprobe ip_tables
/sbin/modprobe ip_conntrack
/sbin/modprobe iptable_filter
/sbin/modprobe iptable_mangle
/sbin/modprobe iptable_nat
/sbin/modprobe ipt_LOG
/sbin/modprobe ipt_limit
/sbin/modprobe ipt_state
/sbin/modprobe ipt_multiport

#/sbin/modprobe ipt_owner
#/sbin/modprobe ipt_REJECT
#/sbin/modprobe ipt_MASQUERADE
#/sbin/modprobe ip_conntrack_ftp
#/sbin/modprobe ip_conntrack_irc
#/sbin/modprobe ip_nat_ftp
#/sbin/modprobe ip_nat_irc

modprobe ip_conntrack_netbios_ns
modprobe ip_conntrack
modprobe ip_conntrack_ftp ports=21
modprobe ip_nat_ftp ports=21

sed -i 's/IPTABLES_MODULES=.*/IPTABLES_MODULES="ip_conntrack_netbios_ns ip_conntrack ip_conntrack_ftp ip_nat_ftp"/' /etc/sysconfig/iptables-config

}

###########################################################################
#
# command line flow control
#
if [ "$1" = "on" ] ; then
	echo "Enabling firewall."
	reset_chains
	# TODO load_modules
	firewall_on
	exit 0
elif [ "$1" = "off" ] ; then
	echo "Disabling firewall."
	reset_chains
	exit 0
elif [ "$1" = "save" ] ; then
	echo "Saving firewall."
	firewall_save
	exit 0
else
	echo "Usage: ${USAGE}"
	exit 0
fi
