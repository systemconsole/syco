#!/usr/bin/env python
'''
Install Wordpress .

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
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-wordpress", install_wordpress, help="Install wordpress and sql.")


def install_wordpress(args):
	'''
	Installation of simple wordpress with mysql
	
	'''

	#Basic setup for database
	#x('yum install mysql-server y')
	#x('/etc/init.d/mysqld restart')
	#x('mysql -e "CREATE DATABASE wordpress;"')
	#x('mysql -e "CREATE USER wpuser@localhost IDENTIFIED BY \'password\';"')
	#x('mysql -e "GRANT ALL PRIVILEGES ON wordpress.* TO wordpressuser@localhost IDENTIFIED BY \'password\';"')
	#x('mysql -e "FLUSH PRIVILEGES;"')


	#Setup webbserver
	x('yum install httpd php php-mysql php-gd -y')
	x('/etc/init.d/httpd restart')

	#Getting and setup wp
	x('wget http://wordpress.org/latest.tar.gz')
	x('tar zxvf latest.tar.gz ')
	x('rsync -avP wordpress/ /var/www/html/')
	x('mkdir /var/www/html/wp-content/uploads')
	x('chown -R apache:apache /var/www/html/*')
	x('chmod -R 774 /var/www/html/*')
	x('iptables -I INPUT 3 -p tcp --dport 80 -j ACCEPT')

	#Fixing wp
	x('mv /var/www/html/wp-config-sample.php /var/www/html/wp-config.php')
	x("sed -i 's/database_name_here/wordpress/g' /var/www/html/wp-config.php")
	x("sed -i 's/username_here/wpuser/g' /var/www/html/wp-config.php")
	x("sed -i 's/password_here/password/g' /var/www/html/wp-config.php")