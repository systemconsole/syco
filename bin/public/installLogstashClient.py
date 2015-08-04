#!/usr/bin/env python
'''
Install logstash clients for sending logs to rabbitmq(Elasticpower installation)

'''

__author__ = "mattias.hemmingsson@fareoffice.com"
__copyright__ = "Copyright 2014, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from general import x
from scopen import scOpen
import app
import version
import os

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1
ES_VERSION='1.4.3'


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-logstash-syslog", install_logstash_syslog, help="Install logstash extension to syslog. [syco install-logstash-syslog 1.5.0]")
    commands.add("uninstall-logstash-syslog", uninstall_logstash_syslog, help="Uninstall logstash extension to syslog.")




def install_logstash_syslog(args):
	'''
	Install the logstash plugin for syslog
	'''
	if len(args) != 2:
		raise Exception("syco install-logstash-syslog 1.5.0")


	if not os.path.isfile('/usr/bin/java'):
		raise Exception("No Java stopping")

	x('yum install wget -y')
	os.system('wget http://download.elastic.co/logstash/logstash/logstash-{0}.tar.gz -O /tmp/logstash.tar.gz'.format(args[1]))
	x('tar zxvf /tmp/logstash.tar.gz -C /opt/')
	x('rm -rf /opt/logstash')
	x('ln -s /opt/logstash* /opt/logstash')
	x('mkdir /etc/logstash')
	x('cp /opt/syco/usr/syco-private/var/logstash/logstash_shipper.conf /etc/logstash/')
	x('cp /opt/syco/usr/syco-private/var/logstash/start/shipper /etc/init.d/')
	x('chmod 775 /etc/init.d/shipper')
	x('chkconfig --add shipper')
	x('chkconfig  shipper on')


def uninstall_logstash_syslog(args):
	'''
	Uninstall the logstash plugin for syslog
	'''
	x('rm -rf /opt/logstash')
	x('rm -rf /etc/lostash')
	x('chkconfig --del shipper')
	x('rm -rf /etc/init.d/shipper')

