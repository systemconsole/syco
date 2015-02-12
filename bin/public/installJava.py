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
JDK_INSTALL_FILE = "jdk-7u40-linux-x64.tar.gz"
JDK_REPO_URL     = "http://packages.fareoffice.com/java/%s" % (JDK_INSTALL_FILE)
JDK_INSTALL_PATH = "/usr/java/jdk1.7.0_40"
JDK_VERSION = "jdk1.7.0_40"

def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-java", install_java, help="Install/configure Java.")


def install_java(args):
	'''
	Installation of the java sdk.
	
	'''

	x('yum install wget -y')
	x('mkdir /opt/syco/installtemp')

	if (not os.access(JDK_INSTALL_PATH, os.F_OK)):
	    os.chdir(app.INSTALL_DIR)
	    if (not os.access(JDK_INSTALL_FILE, os.F_OK)):
	      general.download_file(JDK_REPO_URL)
	
	      x("chmod u+rx " + JDK_INSTALL_FILE)
	
	    if (os.access(JDK_INSTALL_FILE, os.F_OK)):
	          x("tar -zxvf "+JDK_INSTALL_FILE )
	          x("mkdir /usr/java")
	          x("mv "+JDK_VERSION+" /usr/java")
	          x("rm -f /usr/java/default")
	          x("rm -f /usr/java/latest")
	          x("ln -s /usr/java/"+JDK_VERSION+" /usr/java/default")
	          x("ln -s /usr/java/default /usr/java/latest")
	          x("chown root:glassfish -R /usr/java/"+JDK_VERSION)
	          x("chmod 774 -R /usr/java/"+JDK_VERSION)
	          x("chmod 701 /usr/java")
	          x("alternatives --install /usr/bin/javac javac /usr/java/latest/bin/javac 20000")
	          x("alternatives --install /usr/bin/jar jar /usr/java/latest/bin/jar 20000")
	          x("alternatives --install /usr/bin/java java /usr/java/latest/jre/bin/java 20000")
	          x("alternatives --install /usr/bin/javaws javaws /usr/java/latest/jre/bin/javaws 20000")
	          x('chown root:root -R /usr/java/latest')
			  x('chmod 775 -R /usr/java/latest')
	
	
	
	    else:
	      raise Exception("Not able to download " + JDK_INSTALL_FILE)

	x('rm -rf /opt/syco/installtemp')