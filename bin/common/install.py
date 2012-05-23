#!/usr/bin/env python
'''
Functions that will help installing yum and rpm packages.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.1"
__status__ = "Production"

import subprocess

import version
from constant import BOLD, RESET

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 2

def epel_repo():
  '''
  Setup EPEL repository.

  http://ridingthecloud.com/installing-epel-repository-centos-rhel/
  http://www.question-defense.com/2010/04/22/install-the-epel-repository-on-centos-linux-5-x-epel-repo

  '''
  rpm("epel-release-6-6.noarch", "http://ftp.df.lth.se/pub/fedora-epel/6/x86_64/epel-release-6-6.noarch.rpm")

def package(name):
  _package(name, "yum -y install " + name)

def rpm(name, url):
  _package(name, "rpm -Uhv " + url)

def _package(name, command):
  version_obj = version.Version("package-" + name, SCRIPT_VERSION)
  if (not version_obj.is_executed()):
    print("\t" + BOLD + "Command: " + RESET + command)
    if (not is_rpm_installed(name)):
      subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()

    if (is_rpm_installed(name)):
      version_obj.mark_executed()
    else:
      raise Exception("Failed to install " + name + ".")

def is_rpm_installed(name):
    '''
    Check if an rpm package is installed.

    '''
    stdoutdata = subprocess.Popen("rpm -q " + name, shell=True, stdout=subprocess.PIPE).communicate()[0]
    if stdoutdata.strip().find(name) == 0:
      return True
    else:
      return False
