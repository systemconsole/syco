#!/usr/bin/env python
"""
Install Docker.

"""

__author__ = "yursol@fareoffice.com"
__copyright__ = "Copyright 2016, The System Console project"
__maintainer__ = "Yurii Soldak"
__email__ = "yursol@fareoffice.com"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from general import x
import app
import config
import version
from scopen import scOpen
import os

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    commands.add("install-docker", install_docker, help="Install Docker engine.")
    commands.add("verify-docker", verify_docker, help="Verify Docker engine installation.")
    commands.add("uninstall-docker", uninstall_docker, help="Uninstall Docker engine.")


def install_docker(args):
    """Install and configure docker on the local host."""
    app.print_verbose("Install docker version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("Installdocker", SCRIPT_VERSION)
    version_obj.check_executed()

    proxy_host = config.general.get_proxy_host()
    proxy_port = config.general.get_proxy_port()

    #Prepare proxy-access for YUM if needed
    if proxy_host and proxy_port:
        proxy_http="http://%s:%s" % (proxy_host,proxy_port)
        proxy_https="https://%s:%s" % (proxy_host,proxy_port)
        os.environ['http_proxy']=proxy_http
        os.environ['https_proxy']=proxy_https

    x('cp %s/docker/docker.repo /etc/yum.repos.d/docker.repo' % app.SYCO_VAR_PATH)
    x('yum -y install docker-engine')

    x('cp %s/docker/docker /etc/sysconfig/docker' % app.SYCO_VAR_PATH)

    # http://stackoverflow.com/questions/23111631/cannot-download-docker-images-behind-a-proxy
    docker_conf = scOpen(filename='/etc/sysconfig/docker')
    if proxy_host and proxy_port:
        docker_conf.replace('%HTTP_PROXY%', 'export HTTP_PROXY="http://%s:%s"' % (proxy_host, proxy_port))
        docker_conf.replace('%HTTPS_PROXY%', 'export HTTPS_PROXY="https://%s:%s"' % (proxy_host, proxy_port))
    else:
        docker_conf.replace('%HTTP_PROXY%', '')
        docker_conf.replace('%HTTPS_PROXY%', '')

    #FW rule needed to access container through ports
    x('iptables -A syco_output -j DOCKER')
    x('service iptables save')

    x('chkconfig docker on')
    x('service docker start')
    version_obj.mark_executed()


def verify_docker(args):
    """Verify docker installed correctly."""
    x('docker run hello-world 1>&2')


def uninstall_docker(args):
    """Uninstall docker"""
    x('service docker stop')
    x('yum -y remove docker-engine')
    x('rm -f /etc/yum.repos.d/docker.repo') 
    x('rm -f /etc/sysconfig/docker')
    x('rm -rf /var/lib/docker')
