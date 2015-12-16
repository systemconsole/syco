#!/usr/bin/env python
'''
Install Sonar.

'''

__author__ = "Mattias.hemmingsson@fareoffice.com, daniel@cybercow.se"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

from general import x,download_file
from scopen import scOpen
import app
import config
import version


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("install-sonar",   install_sonar,   help="Install Sonar server. version")
    commands.add("uninstall-sonar", uninstall_sonar, help="Uninstall Sonar server.")


def install_sonar(args):
    '''
    Install and configure sonar on the local host.

    '''
    if (len(args) != 2):
      raise Exception("syco install-espower Logstash Version [syco install-sonare 5.0]")
    if os.path.isfile("/bin/java"):
      '''
      Is Java installed ?
      '''
      x('yum install wget unzip -y')
      x('rm -rf /opt/sonarqube')
      download_file('http://dist.sonar.codehaus.org/sonarqube-{0}.zip'.format(args[1]))
      x('mv /opt/syco/installtemp/sonarqube-{0}.zip /opt/sonarqube.zip'.format(args[1]))
      x('unzip /opt/sonarqube.zip')
      x('/opt/sonarqube/bin/linux-x86-64/sonar.sh start')
      x('rm /opt/sonarqube-5.0.zip')
    else:
      print("No java is installed")



def uninstall_sonar(args):
  '''
  Uninstall sonar

  '''
  x('echo "uninstall"')
  x('/opt/sonarqube/bin/linux-x86-64/sonar.sh stop')
  x('rm -rf /opt/sonarqube/')
  
