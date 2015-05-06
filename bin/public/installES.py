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


from general import x
from scopen import scOpen
import app
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1
ES_VERSION='1.4.3'


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-es", install_es, help="Install/configure Elasticsearch.")


def install_es(args):
	'''
	Install setup Elasticsearch
	'''
	x('syco install-java')
	x('yum install wget -y')
	x('wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-'+ES_VERSION +'.noarch.rpm ')
	x('yum localinstall elasticsearch-'+ES_VERSION +'.noarch.rpm -y')
	x('rm -rf elasticsearch-'+ES_VERSION +'.noarch.rpm ')
	x('/etc/init.d/elasticsearch restart')
	x('chkconfig elasticsearch on')



