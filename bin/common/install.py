#!/usr/bin/env python
'''
Functions that will help installing yum, rpm and apt-get packages.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import subprocess

import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def package(name):
  version_obj = version.Version("rpm-" + name, SCRIPT_VERSION)
  if (not version_obj.is_executed()):
    stdoutdata = subprocess.Popen("rpm -qa " + name, shell=True, stdout=subprocess.PIPE).communicate()[0]
    if name not in stdoutdata:
      subprocess.Popen("yum -y install " + name, shell=True).wait()
      # TODO: Need this?
      # time.sleep(1)

    stdoutdata = subprocess.Popen("rpm -qa " + name, shell=True, stdout=subprocess.PIPE).communicate()[0]
    if name not in stdoutdata:
      print "Failed to install " + name
    else:
      version_obj.mark_executed()

def epel_repo():
  '''
  Setup EPEL repository.

  http://ridingthecloud.com/installing-epel-repository-centos-rhel/
  http://www.question-defense.com/2010/04/22/install-the-epel-repository-on-centos-linux-5-x-epel-repo

  '''
  version_obj = version.Version("repo-epel", SCRIPT_VERSION)
  if (not version_obj.is_executed()):
    stdoutdata = subprocess.Popen("rpm -q epel-release-6-5.noarch", shell=True, stdout=subprocess.PIPE).communicate()[0]
    if "package epel-release-6-5.noarch is not installed" in stdoutdata:
      subprocess.Popen("rpm -Uhv http://download.fedora.redhat.com/pub/epel/6/x86_64/epel-release-6-5.noarch.rpm", shell=True, stdout=subprocess.PIPE).communicate()

    stdoutdata = subprocess.Popen("epel-release-6-5.noarch", shell=True, stdout=subprocess.PIPE).communicate()[0]
    if "epel-release-6-5" not in stdoutdata:
      print "Failed to install epel repo."
    else:
      version_obj.mark_executed()
