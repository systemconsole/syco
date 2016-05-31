#!/usr/bin/env python
'''
Install NodeJS server

'''

__author__ = "rikard.stenlund@fareoffice.com"
__copyright__ = "Copyright 2014, The System Console project"
__maintainer__ = "Rikard Stenlund"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import general
from general import x
from scopen import scOpen
import app
import version
import os
import iptables

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
	commands.add("install-node", install_nodejs, help="Install nodejs on server (version tested: 0.12.2)")



def install_nodejs(args):
	if len(args) != 2:
		raise Exception("syco install-nodejs 0.12.2 (or other version)")
	version = args[1]
	x('rm -rf /usr/node')
	x('mkdir /usr/node')
	os.chdir('/usr/node')
	#use general.shell_exec since x(wget) gives an error for each progress output
	general.shell_exec('wget http://nodejs.org/dist/v{0}/node-v{1}.tar.gz'.format(version, version))
	x('tar xzvf node-v* && cd node-v*')
	x('yum install gcc gcc-c++ -y')
	x('cd node-v* && ./configure')
	x('cd node-v* && make')
	x('cd node-v* && make install')
