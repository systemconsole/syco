#!/usr/bin/env python
'''
A module to the CIS audit.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from utils import check_empty, check_equal, check_equal_re, check_equals, check_not_empty, check_return_code, print_header, view_output, print_warning, print_info

#
print_header("4 Network Configuration and Firewalls")

#
print_header("4.1 Modify Network Parameters (Host Only)")

#
print_header("4.1.1 Disable IP Forwarding (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.ip_forward",
    "net.ipv4.ip_forward = 0"
)

#
print_header("4.1.2 Disable Send Packet Redirects (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.conf.all.send_redirects",
    "net.ipv4.conf.all.send_redirects = 0"
)
check_equal(
    "/sbin/sysctl net.ipv4.conf.default.send_redirects",
    "net.ipv4.conf.default.send_redirects = 0"
)

#
print_header("4.2 Modify Network Parameters (Host and Router)")

#
print_header("4.2.1 Disable Source Routed Packet Acceptance (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.conf.all.accept_source_route",
    "net.ipv4.conf.all.accept_source_route = 0"
)
check_equal(
    "/sbin/sysctl net.ipv4.conf.default.accept_source_route",
    "net.ipv4.conf.default.accept_source_route = 0"
)

#
print_header("4.2.2 Disable ICMP Redirect Acceptance (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.conf.all.accept_redirects",
    "net.ipv4.conf.all.accept_redirects = 0"
)
check_equal(
    "/sbin/sysctl net.ipv4.conf.default.accept_redirects",
    "net.ipv4.conf.default.accept_redirects = 0"
)

#
print_header("4.2.3 Disable Secure ICMP Redirect Acceptance (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.conf.all.secure_redirects",
    "net.ipv4.conf.all.secure_redirects = 0"
)
check_equal(
    "/sbin/sysctl net.ipv4.conf.default.secure_redirects",
    "net.ipv4.conf.default.secure_redirects = 0"
)

#
print_header("4.2.4 Log Suspicious Packets (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.conf.all.log_martians",
    "net.ipv4.conf.all.log_martians = 1"
)

check_equal(
    "/sbin/sysctl net.ipv4.conf.default.log_martians",
    "net.ipv4.conf.default.log_martians = 1"
)

#
print_header("4.2.5 Enable Ignore Broadcast Requests (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.icmp_echo_ignore_broadcasts",
    "net.ipv4.icmp_echo_ignore_broadcasts = 1"
)

#
print_header("4.2.6 Enable Bad Error Message Protection (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.icmp_ignore_bogus_error_responses",
    "net.ipv4.icmp_ignore_bogus_error_responses = 1"
)

#
print_header("4.2.7 Enable RFC-recommended Source Route Validation (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.conf.all.rp_filter",
    "net.ipv4.conf.all.rp_filter = 1"
)
check_equal(
    "/sbin/sysctl net.ipv4.conf.default.rp_filter",
    "net.ipv4.conf.default.rp_filter = 1"
)

#
print_header("4.2.8 Enable TCP SYN Cookies (Scored)")
check_equal(
    "/sbin/sysctl net.ipv4.tcp_syncookies",
    "net.ipv4.tcp_syncookies = 1"
)

#
print_header("4.3 Wireless Networking")

#
print_header("4.3.1 Deactivate Wireless Interfaces (Not Scored)")
print_warning("Check manually for wireless interfaces.")
view_output("ifconfig -a")

#
print_header("4.4 Disable IPv6")

#
print_header("4.4.1 Configure IPv6")

#
print_header("4.4.1.1 Disable IPv6 Router Advertisements (Not Scored)")
check_equal(
    "/sbin/sysctl net.ipv6.conf.all.accept_ra",
    'error: "net.ipv6.conf.all.accept_ra" is an unknown key'
)
check_equal(
    "/sbin/sysctl net.ipv6.conf.default.accept_ra",
    'error: "net.ipv6.conf.default.accept_ra" is an unknown key'
)

#
print_header("4.4.1.2 Disable IPv6 Redirect Acceptance (Not Scored)")
check_equal(
    "/sbin/sysctl net.ipv6.conf.all.accept_redirects",
    'error: "net.ipv6.conf.all.accept_redirects" is an unknown key'
)
check_equal(
    "/sbin/sysctl net.ipv6.conf.default.accept_redirects",
    'error: "net.ipv6.conf.default.accept_redirects" is an unknown key'
)

#
print_header("4.4.2 Disable IPv6 (Not Scored)")
check_equals(
    'grep ipv6 /etc/modprobe.d/*',
    (
        'options ipv6 disable=1'
    )
)
check_equal('grep net-pf-10 /etc/modprobe.d/*', 'alias net-pf-10 off')
check_equal(
    "grep NETWORKING_IPV6 /etc/sysconfig/network",
    "NETWORKING_IPV6=no"
)

check_equal(
    "grep IPV6INIT /etc/sysconfig/network",
    "IPV6INIT=no"
)

#
print_header("4.5 Install TCP Wrappers")

#
print_header("4.5.1 Install TCP Wrappers (Not Scored)")
check_equal_re(
    "rpm -q tcp_wrappers",
    "tcp_wrappers-.*"
)

#
print_header("4.5.2 Create /etc/hosts.allow (Not Scored)")
print_warning("Check manually to verify hosts.")
view_output("cat /etc/hosts.allow")

#
print_header("4.5.3 Verify Permissions on /etc/hosts.allow (Scored)")
check_equal(
    'stat -c "%a" /etc/hosts.allow | egrep "644"',
    "644"
)

#
print_header("4.5.4 Create /etc/hosts.deny (Not Scored)")
check_equal(
    'grep "ALL: ALL" /etc/hosts.deny',
    "ALL: ALL"
)

#
print_header("4.5.5 Verify Permissions on /etc/hosts.deny (Scored)")
check_equal(
    'stat -c "%a" /etc/hosts.deny | egrep "644"',
    "644"
)

#
print_header("4.6 Uncommon Network Protocols")

#
print_header("4.6.1 Disable DCCP (Not Scored)")
check_equal('grep "install dccp /bin/true" /etc/modprobe.d/*', 'install dccp /bin/true')
check_equal("/sbin/modprobe -n -v dccp", "install /bin/true")
check_empty("/sbin/lsmod | grep dccp")

#
print_header("4.6.2 Disable SCTP (Not Scored)")
check_equal('grep "install sctp /bin/true" /etc/modprobe.d/*', 'install sctp /bin/true')
check_equals(
    '/sbin/modprobe -n -v sctp',
    (
        None,
        None,
        "install /bin/true"
    )
)
check_empty("/sbin/lsmod | grep sctp")

#
print_header("4.6.3 Disable RDS (Not Scored)")
check_equal('grep "install rds /bin/true" /etc/modprobe.d/*', 'install rds /bin/true')
check_equal("/sbin/modprobe -n -v rds", "install /bin/true")
check_empty("/sbin/lsmod | grep rds")

#
print_header("4.6.4 Disable TIPC (Not Scored)")
check_equal('grep "install tipc /bin/true" /etc/modprobe.d/*', 'install tipc /bin/true')
check_equal("/sbin/modprobe -n -v tipc", "install /bin/true")
check_empty("/sbin/lsmod | grep tipc")

#
print_header("4.7 Enable IPtables (Scored)")
check_equal_re(
    "chkconfig --list iptables",
    "iptables.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
)

#
print_header("4.8 Enable IP6tables (Not Scored)")
check_equal_re(
    "chkconfig --list ip6tables",
    "ip6tables.*0:off.*1:off.*2:on.*3:on.*4:on.*5:on.*6:off"
)
