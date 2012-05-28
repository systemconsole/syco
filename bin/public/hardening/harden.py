#!/usr/bin/env python

__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"




import ConfigParser
import os
import re
from passwords import *
from service import *
from package import *
from ssh import *



# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  '''
  Defines the commands that can be executed through the fosh.py shell script.

  '''
  commands.add("harden",   harden,  help="Harden servers")




def harden():
	#hardenSSH()
	verifySSH()


def copingFile(filname):
	'''
	Scrip for making an copy of an file fore altering file.
	Backupfile will be saved in same location but named .DATE_sycobackup
	'''

def runCmd(cmd):
	print cmd 
	

harden()

