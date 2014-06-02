#!/usr/bin/env python
'''
Installs Standars version



'''

__author__ = "mattias.hemmingsson@elino.se"
__copyright__ = "Copyright 2014, The System Console project"
__maintainer__ = "Mattias Hemmingsson"
__email__ = "syco@cybercow.se"
__credits__ = ["Daniel Lindh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

from general import x
import os
from config import get_devices, get_switches

repo = "git@github.com:mattiashem/syco-util.git"
dest = "/opt/syco-utils"
fabric = "git@github.com:fabric/fabric.git"


def build_commands(commands):	
  commands.add("install-syco-utils", init_git, help="Install syco utils.")
  commands.add("remove-syco-utils", remove_ut, help="Remove the syco utils.")


def install_ut(args):
	'''
	Install the standards on the server
	'''
	print "Installing the syco utils to server"
	x("yum install gcc python-devel python-setuptools -y")
	x("git clone %s %s" % (repo ,dest) )
	x("easy_install pip")
	x("pip install fabric")
	x("pip uninstall pycrypto -y")
	x("pip install PyCrypto==2.3")


def config_fab(args):
	'''
	Setup config files for fabric
	'''
	#File to write
	#try:
	f = open("/opt/syco-utils/Evidence/EvidenceSettings.py", "w")
	#try:	
	host=[]
	switch=[]

	#buildning config file for fab
	f.write("from __future__ import with_statement\n")
	f.write("from fabric.api import local, settings, abort\n")
	f.write("from fabric.contrib.console import confirm\n")
	f.write("from fabric.api import *\n")
	f.write("env.roledefs = {\n")



	for device in get_devices():
		print device.split('-')[0]
		host.append(device)
		f.write("'"+device.split('-')[0]+"':['"+device.split('-')[0]+"'],\n")

	#Adding hosts to fab file	
	f.write("'hosts':"+str(host)+",\n")

	for switches in get_switches():
		switch.append(switches)

	#Adding switches to fab host file
	f.write("'network':"+str(switch)+",\n")
	#Adding test localhost to fab file
	f.write("'localhost':['127.0.0.1'],\n")
	#Closing host list
	f.write("}")
	#Adding network list as well
	f.write("\n\nnetwork="+str(switch)+"\n")
	#Adding apllications list as well
	f.write("\n\napplication=['127.0.0.1']\n")

		#finally:
	f.close()
	x("\cp -f /opt/syco-utils/Evidence/EvidenceSettings.py /opt/syco-utils/ssh-command/sshsettings.py")
	#except IOError:
	#	print "Error"

def init_git(args):
	'''
	Setting up the local git repo for the evidence
	'''
	os.chdir('/opt/syco-utils/Evidence/togit/')
	x("git init")
	x("touch Redme.md")
	x("git add .")
	x("git config --global user.name 'Syco Deamon'")
	x("git config --global user.email syco-deamon@thesyco.net")
	x("git commit --amend --author='Syco Deamon <syco-deamon@thesyco.net>'")
	x("git commit -a -m 'First'")

	# Setting up stabil git branch
	x("git branch stabil")
	x("git checkout stabil")
	x("git add .")
	x("git commit -a -m 'First stabil'")
	#Setting up so running is the default value
	x("git branch running")
	x("git checkout running")
	x("git add .")
	x("git commit -a -m 'First running'")

def remove_ut(args):
	'''
	Install the standards on the server
	'''
	print "Installing the syco utils to server"
	x("rm -rf %s" % (dest) )

