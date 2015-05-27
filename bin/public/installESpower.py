#!/usr/bin/env python
'''
Install DHCP Server

This dhcp server is mainly used to get KVM guest installation to work with
kickstarts.

http://www.yolinux.com/TUTORIALS/DHCP-Server.html
http://www.linuxhomenetworking.com/wiki/index.php/Quick_HOWTO_:_Ch08_:_Configuring_the_DHCP_Server
http://www.howtoforge.com/dhcp_server_linux_debian_sarge

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
CONF_SOURCE='/opt/syco/usr/syco-private/var/'

def build_commands(commands):
    commands.add("install-espower", install_espower, help="Install power modules for elastcisearch")
    commands.add("uninstall-espower", uninstall_espower, help="Uninstall the power modules for elastic search")


def install_espower(args):
	'''
	Installation of Elastic search passing rule
	
	'''
	install_rabbit()
	install_logstash()
	config_rabbitmq()
	config_logstash()
	

	print("Go to http://ip-address:15672 for rabbit mq ")

def uninstall_espower(args):
	x('yum remove rabbitmq-server -y')
	x('yum remove erlang -y')
	x('rm -rf /opt/logstash')
	x('rm -rf /etc/logstash')
	x('rm -rf /etc/rabbitmq')




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
	x('adduse logstash')
	x('cp -r %slogstash /etc/' %CONF_SOURCE)
	x('chown logstash:logstash -R /opt/logstash')
	x('cp /opt/syco/usr/syco-private/var/rabbitmq/start/shipper /etc/init.d/')
	x('cp /opt/syco/usr/syco-private/var/rabbitmq/start/index /etc/init.d/')
	x('chkconfig --add shipper')
	x('chkconfig --add index')
	x('chkconfig shipper on')
	x('chkconfig index on')
	x('/etc/init.d/shipper start')
	x('/etc/init.d/index start')

def config_rabbitmq():
	'''
	There are now defult config for logstash
	Copy config from
	1. First from syco-private
	2. syco var defult config
	'''
	x('mkdir -p /etc/rabbitmq/ssl/private')
	x('openssl req -x509 -config /opt/syco/usr/syco-private/var/rabbitmq/ssl/openssl.cnf -newkey rsa:4096 -days 3650 -out /etc/rabbitmq/ssl/cacert.pem -outform PEM -subj /CN=RabbitMQ/ -nodes')
	x('openssl x509 -in /etc/rabbitmq/ssl/cacert.pem -out /etc/rabbitmq/ssl/cacert.cer -outform DER')
	x('openssl genrsa -out /etc/rabbitmq/ssl/key.pem 4096')
	x('cp /etc/rabbitmq/ssl/private/* /etc/rabbitmq/ssl/')
	x('openssl req -new -key /etc/rabbitmq/ssl/key.pem -out /etc/rabbitmq/ssl/req.pem -outform PEM -subj /CN=$(hostname)/O=server/ -nodes')
	x('touch /etc/rabbitmq/ssl/index.txt')
	x('echo 01 > /etc/rabbitmq/ssl/serial')
	x('openssl ca -config /opt/syco/usr/syco-private/var/rabbitmq/ssl/openssl.cnf -in /etc/rabbitmq/ssl/req.pem -out /etc/rabbitmq/ssl/cert.pem -notext -batch -extensions server_ca_extensions')
	x('openssl pkcs12 -export -out /etc/rabbitmq/ssl/keycert.p12 -in /etc/rabbitmq/ssl/cert.pem -inkey /etc/rabbitmq/ssl/key.pem -passout pass:MySecretPassword')



	x('cp -r %srabbitmq /etc/' %CONF_SOURCE)
	
	x('/etc/init.d/rabbitmq-server restart')
	x('iptables -I INPUT 3 -p tcp --dport 5671 -j ACCEPT')
	x('iptables -I INPUT 3 -p tcp --dport 15672 -j ACCEPT')
	x('setsebool -P nis_enabled 1')
