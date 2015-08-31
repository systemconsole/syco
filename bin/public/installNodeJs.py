#!/usr/bin/env python
'''
Install NodeJS server

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


def build_commands(commands):
    commands.add("install-nodejs", install_nodejs, help="Install nodejs on server (install-nodejs 10.4)")
    commands.add("deploy-nodejs", deploy_nodejs, help="deploy github app to server")


def install_nodejs(args):

    if len(args) != 2:
        raise Exception("syco install-nodejs [version]")

    x('yum install wget gcc-c++ -y')
    os.chdir('/usr/src')
    x('wget http://nodejs.org/dist/v0.{0}/node-v0.{0}.tar.gz -O /usr/src/nodejs_latest.tar.gz'.format(args[1]))
    x('tar -zxvf nodejs_latest.tar.gz')
    x('rm -rf nodejs')
    x('mv node-v* nodejs')
    os.chdir('/usr/src/nodejs')
    x('./configure')
    x('make')
    x('make install')
    x('/usr/local/bin/node --version')

    #Node installed doing setup
    setup_node()


def setup_node():
    """
    Setup nodejs for deployments
    """
    #Installing nodejs modules for system
    x('/usr/local/bin/npm -g install express express-generator supervisor')

    # Config Apache to proxy all info to port 3000
    # Requires precious install of apache, e.g. syco install-httpd
    x('cp /opt/syco/var/nodejs/httpd/nodejs.conf /etc/httpd/conf.d/')


def deploy_nodejs(args):
    """
    Deploying a nodejs node from github to server
    """
    if len(args) != 2:
        raise Exception("syco deply-nodejs mattiashem/r-pi ")
    #Getting app from git
    os.chdir('/var/www/html')
    x('git clone git@github.com:{0}'.format(args[1]))

    #Getting the app name
    apps = args[1].split('/')
    app=apps[1]
    os.chdir('/var/www/html/{0}'.format(app))
    x('supervisor ./bin/www')
