#!/usr/bin/env python

__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"


import ConfigParser
import os
import re

from hardening.passwords import hardenPassword
from hardening.service import serviceOff
from hardening.package import removePackage
from hardening.ssh import hardenSSH, verifySSH
from hardening.network import network, verify_network
from hardening.syslog import syslog, verify_syslog, add_sysloghost
from hardening.permissions import chmod_folders, chmod_files, verify_chmod_files, verify_no_rouge_files, onlyRoot_console, lockdown_pysical, setting_dmask, disble_coredumps, disable_wheelsu
from hardening.auditd import auditd
from hardening.antivirus import install_av


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1


def build_commands(commands):
  '''
  Defines the commands that can be executed through the fosh.py shell script.

  '''
  commands.add("harden",   harden,  help="Harden servers")
  commands.add("harden_ssh",   harden,  help="Harden SSH server and client")
  commands.add("harden_verify",   harden,  help="Verify that server is harden")


def harden(args):
	'''
	Harden server by running harden scrips located in hardening folder.
	Configfile for scripts loctaed in syco/var/hardening
	'''
	removePackage()
	serviceOff()
	lockdown_pysical()
	disble_coredumps()
	disable_wheelsu()
	network()
	syslog()
	add_sysloghost()
	chmod_files()
	chmod_folders()
	onlyRoot_console()
	lockdown_pysical()	
	setting_dmask()
	hardenPassword()
	auditd()
	install_av()


def harden_ssh(args):
	'''
	Harden SSH server.
	Located sepertae to be able to run on virtaul server after kvm install
	'''
	hardenSSH()



def harden_verify(args):
	'''
	Verify that system is harden 
	'''
	verify_syslog()
	verify_network()
	verify_chmod_files()
	verify_no_rouge_files()



