#!/usr/bin/env python
'''
Install/update Elastic Passer.

Recives logs and que logs and then pass to elasticsearch.

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
LOG_SOURCE='/opt/syco/usr/syco-private/var/'


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-espasser", install_espass, help="Install Elasticsearch Passer.(req epel,java)")


def install_espass(args):
	'''
	Installation of Elastic search passing rule
	
	'''
	install_rabbit()
	install_logstash()
	config_logstash()
	config_rabbitmq()


	print("Go to http://ip-address:15672 for rabbit mq ")

def install_rabbit():
	'''
	Installa and setup the rabbit mq server.
	'''


	#check if epel is install else installed
	if not os.path.isfile("yum install rabbitmq-server -y/etc/yum.repos.d/epel.repo"):
		x('yum localinstall http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm -y')
	x('yum install erlang -y')
	x('rpm --import http://www.rabbitmq.com/rabbitmq-signing-key-public.asc')
	x('yum install rabbitmq-server -y')



def install_logstash():
    '''
    Download and install logstash
    '''
    x("curl -O  https://download.elasticsearch.org/logstash/logstash/logstash-1.4.2.tar.gz")
    x('mv logstash-1.4.2.tar.gz /opt/logstash.tar.gz')
    x('tar -zxvf /opt/logstash.tar.gz -C /opt/')
    x('rm /opt/logstash.tar.gz')
    x('rm -rf /opt/logstash')
    x('ln -s /opt/logstash-1* /opt/logstash')



def config_logstash():
	'''
	There are now defult config for logstash
	Copy config from
	1. First from syco-private
	2. syco var defult config
	''' 

	x('cp -r %slogstash /etc/' %LOG_SOURCE)


def config_rabbitmq():
	'''
	There are now defult config for logstash
	Copy config from
	1. First from syco-private
	2. syco var defult config
	'''
	x('cp -r %srabbitmq /etc/' %LOG_SOURCE)
	x('/etc/init.d/rabbitmq-server restart')
	x('iptables -I INPUT 3 -p tcp --dport 5671 -j ACCEPT')
	x('iptables -I INPUT 3 -p tcp --dport 15672 -j ACCEPT')
    x('setsebool -P nis_enabled 1')
