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
print_header("2. OS Services")

#
print_header("2.1 Remove Legacy Services")

#
print_header("2.1.1 Remove telnet-server (Scored)")
check_equal(
    "rpm -q telnet-server",
    "package telnet-server is not installed"
)

#
print_header("2.1.2 Remove telnet Clients (Scored)")
check_equal(
    "rpm -q telnet",
    "package telnet is not installed"
)

#
print_header("2.1.3 Remove rsh-server (Scored)")
check_equal(
    "rpm -q rsh-server",
    "package rsh-server is not installed"
)

#
print_header("2.1.4 Remove rsh (Scored)")
check_equal(
    "rpm -q rsh",
    "package rsh is not installed"
)

#
print_header("2.1.5 Remove NIS Client (Scored)")
check_equal(
    "rpm -q ypbind",
    "package ypbind is not installed"
)

#
print_header("2.1.6 Remove NIS Server (Scored)")
check_equal(
    "rpm -q ypserv",
    "package ypserv is not installed"
)

#
print_header("2.1.7 Remove tftp (Scored)")
check_equal(
    "rpm -q tftp",
    "package tftp is not installed"
)

#
print_header("2.1.8 Remove tftp-server (Scored)")
check_equal(
    "rpm -q tftp-server",
    "package tftp-server is not installed"
)

#
print_header("2.1.9 Remove talk (Scored)")
check_equal(
    "rpm -q talk",
    "package talk is not installed"
)

#
print_header("2.1.10 Remove talk-server (Scored)")
check_equal(
    "rpm -q talk-server",
    "package talk-server is not installed"
)

#
print_header("2.1.11 Remove xinetd (Scored)")
check_equal(
    "rpm -q xinetd",
    "package xinetd is not installed"
)

#
print_header("2.1.12 Disable chargen-dgram (Scored)")
check_equal(
    "rpm -q chargen-dgram",
    "package chargen-dgram is not installed"
)

#
print_header("2.1.13 Disable chargen-stream (Scored)")
check_equal(
    "rpm -q chargen-stream",
    "package chargen-stream is not installed"
)

#
print_header("2.1.14 Disable daytime-dgram (Scored)")
check_equal(
    "rpm -q daytime-dgram",
    "package daytime-dgram is not installed"
)

#
print_header("2.1.15 Disable daytime-stream (Scored)")
check_equal(
    "rpm -q daytime-stream",
    "package daytime-stream is not installed"
)

#
print_header("2.1.16 Disable echo-dgram (Scored)")
check_equal(
    "rpm -q echo-dgram",
    "package echo-dgram is not installed"
)

#
print_header("2.1.17 Disable echo-stream (Scored)")
check_equal(
    "rpm -q echo-stream",
    "package echo-stream is not installed"
)

#
print_header("2.1.18 Disable tcpmux-server (Scored)")
check_equal(
    "rpm -q tcpmux-server",
    "package tcpmux-server is not installed"
)
