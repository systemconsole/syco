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
import config
import version
from constant import BOLD, RESET
from augeas import Augeas


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 3


def epel_repo():
    """
    Setup EPEL repository.
    """

    # Check if epel is already installed and enabled
    augeas = Augeas(x)
    epel_enabled = augeas.find_values('/files/etc/yum.repos.d/epel.repo/epel/enabled')
    if len(epel_enabled) != 1 or epel_enabled[0] != '1':
        x("yum install -y epel-release")
        augeas.set_enhanced('/files/etc/yum.repos.d/epel.repo/epel/enabled', '1')


def rforge_repo():
    """
    Install RPMForge

    http://wiki.centos.org/AdditionalResources/Repositories/RPMForge/#head-f0c3ecee3dbb407e4eed79a56ec0ae92d1398e01

    """
    package = "rpmforge-release-0.5.2-2.el6.rf.x86_64"
    fn = "http://packages.sw.be/rpmforge-release/rpmforge-release-0.5.3-1.el6.rf.x86_64.rpm"

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

    proxy_host = config.general.get_proxy_host()
    proxy_port = config.general.get_proxy_port()

    """Install HP yum repo for hp-health and fix symantec intermediate certificate error"""
    x("update-ca-trust enable")
    x("""cat > /etc/pki/ca-trust/source/anchors/SymantecServerCA-G4.pem << EOF
-----BEGIN CERTIFICATE-----
MIIFODCCBCCgAwIBAgIQUT+5dDhwtzRAQY0wkwaZ/zANBgkqhkiG9w0BAQsFADCB
yjELMAkGA1UEBhMCVVMxFzAVBgNVBAoTDlZlcmlTaWduLCBJbmMuMR8wHQYDVQQL
ExZWZXJpU2lnbiBUcnVzdCBOZXR3b3JrMTowOAYDVQQLEzEoYykgMjAwNiBWZXJp
U2lnbiwgSW5jLiAtIEZvciBhdXRob3JpemVkIHVzZSBvbmx5MUUwQwYDVQQDEzxW
ZXJpU2lnbiBDbGFzcyAzIFB1YmxpYyBQcmltYXJ5IENlcnRpZmljYXRpb24gQXV0
aG9yaXR5IC0gRzUwHhcNMTMxMDMxMDAwMDAwWhcNMjMxMDMwMjM1OTU5WjB+MQsw
CQYDVQQGEwJVUzEdMBsGA1UEChMUU3ltYW50ZWMgQ29ycG9yYXRpb24xHzAdBgNV
BAsTFlN5bWFudGVjIFRydXN0IE5ldHdvcmsxLzAtBgNVBAMTJlN5bWFudGVjIENs
YXNzIDMgU2VjdXJlIFNlcnZlciBDQSAtIEc0MIIBIjANBgkqhkiG9w0BAQEFAAOC
AQ8AMIIBCgKCAQEAstgFyhx0LbUXVjnFSlIJluhL2AzxaJ+aQihiw6UwU35VEYJb
A3oNL+F5BMm0lncZgQGUWfm893qZJ4Itt4PdWid/sgN6nFMl6UgfRk/InSn4vnlW
9vf92Tpo2otLgjNBEsPIPMzWlnqEIRoiBAMnF4scaGGTDw5RgDMdtLXO637QYqzu
s3sBdO9pNevK1T2p7peYyo2qRA4lmUoVlqTObQJUHypqJuIGOmNIrLRM0XWTUP8T
L9ba4cYY9Z/JJV3zADreJk20KQnNDz0jbxZKgRb78oMQw7jW2FUyPfG9D72MUpVK
Fpd6UiFjdS8W+cRmvvW1Cdj/JwDNRHxvSz+w9wIDAQABo4IBYzCCAV8wEgYDVR0T
AQH/BAgwBgEB/wIBADAwBgNVHR8EKTAnMCWgI6Ahhh9odHRwOi8vczEuc3ltY2Iu
Y29tL3BjYTMtZzUuY3JsMA4GA1UdDwEB/wQEAwIBBjAvBggrBgEFBQcBAQQjMCEw
HwYIKwYBBQUHMAGGE2h0dHA6Ly9zMi5zeW1jYi5jb20wawYDVR0gBGQwYjBgBgpg
hkgBhvhFAQc2MFIwJgYIKwYBBQUHAgEWGmh0dHA6Ly93d3cuc3ltYXV0aC5jb20v
Y3BzMCgGCCsGAQUFBwICMBwaGmh0dHA6Ly93d3cuc3ltYXV0aC5jb20vcnBhMCkG
A1UdEQQiMCCkHjAcMRowGAYDVQQDExFTeW1hbnRlY1BLSS0xLTUzNDAdBgNVHQ4E
FgQUX2DPYZBV34RDFIpgKrL1evRDGO8wHwYDVR0jBBgwFoAUf9Nlp8Ld7LvwMAnz
Qzn6Aq8zMTMwDQYJKoZIhvcNAQELBQADggEBAF6UVkndji1l9cE2UbYD49qecxny
H1mrWH5sJgUs+oHXXCMXIiw3k/eG7IXmsKP9H+IyqEVv4dn7ua/ScKAyQmW/hP4W
Ko8/xabWo5N9Q+l0IZE1KPRj6S7t9/Vcf0uatSDpCr3gRRAMFJSaXaXjS5HoJJtG
QGX0InLNmfiIEfXzf+YzguaoxX7+0AjiJVgIcWjmzaLmFN5OUiQt/eV5E1PnXi8t
TRttQBVSK/eHiXgSgW7ZTaoteNTCLD0IX4eRnh8OsN4wUmSGiaqdZpwOdgyA8nTY
Kvi4Os7X1g8RvmurFPW9QaAiY4nxug9vKWNmLT+sjHLF+8fk1A/yO0+MKcc=
-----END CERTIFICATE-----
EOF""")
    x("update-ca-trust extract")

    x("rpm --import --httpproxy %s --httpport %s https://downloads.linux.hpe.com/SDR/hpPublicKey1024.pub" % (proxy_host, proxy_port))
    x("rpm --import --httpproxy %s --httpport %s https://downloads.linux.hpe.com/SDR/hpPublicKey2048.pub" % (proxy_host, proxy_port))
    x("rpm --import --httpproxy %s --httpport %s https://downloads.linux.hpe.com/SDR/hpPublicKey2048_key1.pub" % (proxy_host, proxy_port))
    x("rpm --import --httpproxy %s --httpport %s https://downloads.linux.hpe.com/SDR/hpePublicKey2048_key1.pub" % (proxy_host, proxy_port))

    x("""cat > /etc/yum.repos.d/hp.repo << EOF
[HP-Proliant]
name=Software Delivery Repository \$releasever - \$basearch
baseurl=https://downloads.linux.hpe.com/SDR/downloads/ServicePackforProLiant/RedHat/\$releasever/\$basearch/current/
enabled=1
gpgcheck=1
gpgkey=https://downloads.linux.hpe.com/SDR/downloads/ServicePackforProLiant/GPG-KEY-ServicePackforProLiant
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
