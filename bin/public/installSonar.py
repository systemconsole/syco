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

from general import x
from scopen import scOpen
import app
import config
import version


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
    commands.add("install-sonar",   install_sonar,   help="Install Sonar server.")
    commands.add("uninstall-sonar", uninstall_sonar, help="Uninstall Sonar server.")


def install_sonar(args):
    '''
    Install and configure sonar on the local host.

    '''
    if os.path.isfile("/bin/java"):
      '''
      Is Java installed ?
      '''
      x('yum install wget unzip -y')
      os.system('wget http://dist.sonar.codehaus.org/sonarqube-5.0.zip')
      x('mv sonarqube-5.0.zip /opt/sonarqube-5.0.zip')
      x('unzip /opt/sonarqube-5.0.zip')
      x('ln -s /opt/sonarqube-5.0 /opt/sonarqube')
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
  
