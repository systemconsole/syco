#!/usr/bin/env python
'''
Install of Utils for system

This installation file is for adding differnt utils to the syco system.

- Reminder
Reminder is an automted script for reminding and helping sysop what is happening.
defult set up is to match PCI reqerments.

Script will shedule task with crontab and use private folder to send emails to email list.
For altering email that are sent use template in syco-private

: Remind oncall who is oncall
: Daily tasks
: Weekly tasks
: Montly tasks
: Quarterly tasks


'''

__author__ = "daniel@cybercow.se, matte@elino.se"
__copyright__ = "Copyright 2012, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import string

from config import get_servers
from general import generate_password, get_install_dir
from general import x
from installMysql import install_mysql, mysql_exec
from scopen import scOpen
import app
import config
import general
import installLogrotate
import iptables
import mysqlUtils
import net
import version

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 2


def build_commands(commands):
    '''
    Defines the commands that can be executed through the syco.py shell script.

    '''
    commands.add("utils-reminder",          install_reminder,   help="Install the reminder script")


def install_reminder(args):
	'''
	Install the reminder utils
	'''



