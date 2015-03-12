#!/usr/bin/env python
'''
Install/update Java.

'''

__author__ = "mattias.hemmingsson@fareoffice.com"
__copyright__ = "Copyright 2014, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
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

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

# http://www.oracle.com/technetwork/java/javase/downloads/index.html
# go to http://www.oracle.com/technetwork/java/javase/downloads/index.html and get the correct
# jdp version and extension nummer.
#
JDK_VERSION = "8u31"
JDK_EXTENSION ="b13"
def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-java", install_java, help="Install/configure Java.")


def install_java(args):
	'''
	Installation of the java sdk.
	
	'''

	if (len(args) != 3):
		raise Exception("syco install-mysql b13 8u31 jdk_extension, jdk_version http://www.oracle.com/technetwork/java/javase/downloads/index.html")
	JDK_VERSION = args[2]
	JDK_EXTENSION = args[1]
	x('yum install wget -y')
	os.system('wget --no-check-certificate --no-cookies --header "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/'+JDK_VERSION+'-'+JDK_EXTENSION+'/jdk-'+JDK_VERSION+'-linux-x64.rpm')
	x('yum localinstall jdk-'+JDK_VERSION+'-linux-x64.rpm -y')
	x('rm -rf jdk-'+JDK_VERSION+'-linux-x64.rpm')
	x('java -version')

	