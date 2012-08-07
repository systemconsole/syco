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
__version__ = "1.0.2"
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
  package = "epel-release-6-7.noarch"
  fn = "http://ftp.df.lth.se/pub/fedora-epel/6/x86_64/epel-release-6-7.noarch.rpm"
  rpm(package, fn)


def rforge_repo():
  '''
  Install RPMForge

  http://wiki.centos.org/AdditionalResources/Repositories/RPMForge/#head-f0c3ecee3dbb407e4eed79a56ec0ae92d1398e01

  '''
  package = "rpmforge-release-0.5.2-2.el6.rf.x86_64"
  fn = "http://packages.sw.be/rpmforge-release/rpmforge-release-0.5.2-2.el6.rf.x86_64.rpm"

  if not is_rpm_installed(package):
    _yum_protect_base()


    # Install DAG's GPG key
    x("rpm --import http://apt.sw.be/RPM-GPG-KEY.dag.txt")

    # Verify the package you have downloaded
    # Security warning: The rpmforge-release package imports GPG keys into your RPM
    # database. As long as you have verified the md5sum of the key injection package,
    # and trust Dag, et al., then it should be as safe as your trust of them extends.
    if "(sha1) dsa sha1 md5 gpg OK" not in x("rpm -K %s" % fn):
      raise Exception("Invalid checksum for package %s." % fn)

    # Download rpmforge packages.
    rpm(package, fn)


def _yum_protect_base():
  '''
  Enable yum protect base

  http://wiki.centos.org/PackageManagement/Yum/ProtectBase/

  '''
  package("yum-plugin-protectbase")


def package(name):
  _package(name, "yum -y install " + name)


def rpm(name, url):
  _package(name, "rpm -Uhv " + url)


def _package(name, command):
  version_obj = version.Version("package-" + name, SCRIPT_VERSION)
  if (not version_obj.is_executed()):
    print("\t" + BOLD + "Command: " + RESET + command)
    if (not is_rpm_installed(name)):
      x(command)

    if (is_rpm_installed(name)):
      version_obj.mark_executed()
    else:
      raise Exception("Failed to install " + name + ".")


def is_rpm_installed(name):
    '''
    Check if an rpm package is installed.

    '''
    stdoutdata = x("rpm -q " + name)
    if stdoutdata.strip().find(name) == 0:
      return True
    else:
      return False


def rpm_remove(name):
  '''Remove rpm packages'''
  if is_rpm_installed(name):
    command = "rpm -e %s" % name
    x(command)


def x(cmd):
  print("\t" + BOLD + "Command: " + RESET + cmd)
  p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
  stdoutdata = p.communicate()[0]
  return stdoutdata
