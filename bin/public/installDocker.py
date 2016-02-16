#!/usr/bin/env python
'''
Install Docker.

'''

__author__ = "yursol@fareoffice.com"
__copyright__ = "Copyright 2016, The System Console project"
__maintainer__ = "Yurii Soldak"
__email__ = "yursol@fareoffice.com"
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
    commands.add("install-docker",   install_docker,   help="Install Docker engine.")
    commands.add("verify-docker",   verify_docker,   help="Verify Docker engine installation.")
    commands.add("uninstall-docker", uninstall_docker, help="Uninstall Docker engine.")


def install_docker(args):
    '''
    Install and configure docker on the local host.
    '''
    
    x('cp /opt/syco/var/docker/docker.repo /etc/yum.repos.d/docker.repo')
    x('yum -y install docker-engine')

    x('cp /opt/syco/var/docker/docker /etc/sysconfig/docker')

    x('chkconfig docker on')
    x('service docker start')

def verify_docker(args):
    '''
    Verify docker installed correctly.
    '''
    
    x('docker run hello-world 1>&2')

def uninstall_docker(args):
    '''
    Uninstall docker
    '''
    
    x('service docker stop')
    x('yum -y remove docker-engine')
    x('rm -f /etc/yum.repos.d/docker.repo') 
    x('rm -f /etc/sysconfig/docker')
    x('rm -rf /var/lib/docker')
