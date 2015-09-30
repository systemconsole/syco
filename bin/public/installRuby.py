#!/usr/bin/env python
'''
Install ruby.
Using RPM package maintained by Fareoffice at:
https://github.com/fareoffice/ruby-rpm-el6-centos

'''

__author__ = "mikael.hellman@fareoffice.com"
__copyright__ = "Copyright 2015, The System Console project"
__maintainer__ = "Mikael Hellman"
__email__ = "syco@cybercow.se"
__credits__ = ["Neo in The Matrix, he made it all possible."]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import general
from general import x
import app
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

RUBY_VERSION = "2.2.2"

def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("install-ruby", install_ruby, help="Install ruby version: " + RUBY_VERSION)

def install_ruby(args):
    '''
    Install ruby
	
    '''
    app.print_verbose("Install ruby script-version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallRuby", SCRIPT_VERSION)
    version_obj.check_executed()    
    x('rpm -iv https://github.com/fareoffice/ruby-rpm-el6-centos/raw/master/build/ruby-2.2.2-1.el6.x86_64.rpm')

