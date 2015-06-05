#!/usr/bin/env python
'''
Install/configure Elasticsearch.

'''

__author__ = "mattias.hemmingsson@fareoffice.com"
__copyright__ = "Copyright 2014, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from general import x,download_file
from scopen import scOpen
import app
import version
import os
import urllib2


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1
ES_VERSION='1.5.2'


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-es", install_es, help="Install/configure Elasticsearch [install-es 1.5.2].")


def install_es(args):
	'''
	Install setup Elasticsearch
	'''
	if not os.path.isfile('/usr/bin/java'):
		raise Exception("No Java stopping")

	if (len(args) != 2):
		raise Exception("syco install-es VERSION [syco install-es 1.5.2]")

	ES_VERSION=args[1]
	#getting and setting up md5
	sha1ES_got=urllib2.urlopen('https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-'+ES_VERSION +'.noarch.rpm.sha1.txt')
	sha1ES= sha1ES_got.read().split(' ')[0]
	x('yum install wget -y')
	download_file('https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-'+ES_VERSION +'.noarch.rpm',sha1=sha1ES)
	x('yum localinstall  /opt/syco/installtemp/elasticsearch-'+ES_VERSION +'.noarch.rpm -y')
	x('/etc/init.d/elasticsearch restart')
	x('chkconfig elasticsearch on')



