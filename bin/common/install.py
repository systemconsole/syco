#!/usr/bin/env python
"""
Functions that will help installing yum and rpm packages.

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.3"
__status__ = "Production"

import os
import subprocess

import version
from constant import BOLD, RESET

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 3


def epel_repo():
    """
    Setup EPEL repository.

    http://ridingthecloud.com/installing-epel-repository-centos-rhel/
    http://www.question-defense.com/2010/04/22/install-the-epel-repository-on-centos-linux-5-x-epel-repo

    """
    package = "epel-release-6-8.noarch"
    fn = "http://mirrors.se.eu.kernel.org/fedora-epel/6/x86_64/epel-release-6-8.noarch.rpm"
    rpm(package, fn)


def rforge_repo():
    """
    Install RPMForge

    http://wiki.centos.org/AdditionalResources/Repositories/RPMForge/#head-f0c3ecee3dbb407e4eed79a56ec0ae92d1398e01

    """
    package = "rpmforge-release-0.5.2-2.el6.rf.x86_64"
    fn = "http://packages.sw.be/rpmforge-release/rpmforge-release-0.5.2-2.el6.rf.x86_64.rpm"

    if not is_rpm_installed(package):
        _yum_protect_base()

        # Install DAG's GPG key
        x("rpm --import http://apt.sw.be/RPM-GPG-KEY.dag.txt")

        # Verify the package you have downloaded
        # Security warning: The rpmforge-release package imports GPG keys into
        # your RPM database. As long as you have verified the md5sum of the key
        # injection package, and trust Dag, et al., then it should be as safe
        # as your trust of them extends.
        if "(sha1) dsa sha1 md5 gpg OK" not in x("rpm -K %s" % fn):
            raise Exception("Invalid checksum for package %s." % fn)

        # Download rpmforge packages.
        rpm(package, fn)


def hp_repo():
    """Install HPs Software Delivery Repository Repo"""
    x("rpm --import http://downloads.linux.hp.com/SDR/hpPublicKey1024.pub")
    x("rpm --import http://downloads.linux.hp.com/SDR/hpPublicKey2048.pub")
    x("rpm --import http://downloads.linux.hp.com/SDR/hpPublicKey2048_key1.pub")

    x("""cat > /etc/yum.repos.d/hp.repo << EOF
[HP-Proliant]
name=Software Delivery Repository \$releasever - \$basearch
baseurl=http://downloads.linux.hpe.com/SDR/repo/spp/rhel/\$releasever/\$basearch/current/
enabled=1
gpgcheck=0
gpgkey=https://downloads.linux.hpe.com/SDR/repo/spp/GPG-KEY-SPP
EOF""")



def atomic_repo():
    """
    Setup ATOMIC repository.

    Used for openvas, ossec etc.

    """
    # Must be imported in the function, because install.py should be possible
    # to import before app and general.
    import app
    import general

    app.print_verbose("Adding atomic repo for yum.")
    general.shell_exec(
        "wget -q -O - http://www.atomicorp.com/installers/atomic | sh",
        events={'(?i)\[Default: yes\]':'\n'}
    )

    if (not os.access("/etc/yum.repos.d/atomic.repo", os.F_OK)):
        raise Exception("You need to install the atomic repo first.")


def _yum_protect_base():
    """
    Enable yum protect base

    http://wiki.centos.org/PackageManagement/Yum/ProtectBase/

    """
    package("yum-plugin-protectbase")


def package(name):
    _package(name, "yum -y install " + name)


def packages(package_names):
    """
    Yum install packages

    package_names - space separated list of packages to install
    """
    for name in package_names.split():
        package(name)


def rpm(name, url):
    _package(name, "rpm -Uhv " + url)


def _package(name, command):
    version_obj = version.Version("package-" + name, 1)
    if not version_obj.is_executed():
        print("\t" + BOLD + "Command: " + RESET + command)
        if not is_rpm_installed(name):
            x(command)

        if is_rpm_installed(name):
            version_obj.mark_executed()
        else:
            raise Exception("Failed to install " + name + ".")


def is_rpm_installed(name):
    """
    Check if an rpm package is installed.

    """
    stdoutdata = x("rpm -q " + name)
    if stdoutdata.strip().find(name) == 0:
        return True
    else:
        return False


def rpm_remove(name):
    """Remove rpm packages"""
    if is_rpm_installed(name):
        command = "rpm -e %s" % name
        x(command)


def x(cmd):
    print("\t" + BOLD + "Command: " + RESET + cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    stdoutdata = p.communicate()[0]
    return stdoutdata
