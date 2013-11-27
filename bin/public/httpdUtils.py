#!/usr/bin/env python
'''
Utils for managing httpd

'''

__author__ = "Kristofer Borgstrom"
__copyright__ = "Copyright 2013, The System Console project"
__maintainer__ = "Kristofer Borgstrom"
__email__ = "kristofer@fareoffice.com"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import app
from app import print_verbose
from general import x
from installMysql import mysql_exec
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
  commands.add("httpd-toggle-mod-sec", toggle_mod_sec, help="Turn mod security on or off")

def toggle_mod_sec(args):

    ##Check args
    if (len(args) != 2 or (args[1].lower() != "on" and args[1].lower() != "off")):
        raise Exception("Invalid arguments. syco httpd-toggle-mod-sec [on|off]")

    CONF_FILE = "/etc/httpd/conf.d/003-modsecurity.conf"

    if args[1].lower() == "on":
        x("sed -i '/SecRuleEngine On/ s/^#//' " + CONF_FILE)
        x("sed -i '/SecRequestBodyAccess On/ s/^#//' " + CONF_FILE)

    if args[1].lower() == "off":
        x("sed -i '/SecRuleEngine On/ s/^/#/' " + CONF_FILE)
        x("sed -i '/SecRequestBodyAccess On/ s/^/#/' " + CONF_FILE)

    x("service httpd graceful")

def toggle_apache_mod(apache_mod, turn_on):

    CONF_FILE = "/etc/httpd/conf/httpd.conf"

    ##Check args
    if (not isinstance(turn_on, bool)):
        raise Exception("Invalid argument, expected a boolean value")

    if turn_on:
        x("sed -i '/" + apache_mod + "/ s/^#//' " + CONF_FILE)
    else:
        x("sed -i '/" + apache_mod + "/ s/^/#/' " + CONF_FILE)