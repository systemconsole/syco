#!/usr/bin/env python
'''
Setup permissions - part of the hardening.

- Chmod folder according to configfile
- Chmod files according to confgifiles
- Verfiy chmod files settings
- Finding rouge files on system
- Set only root login from console
- Lock down singel boot function
- Set dmask on the server
- Disabling core dumps on system
- Disabling su for users in wheel group (cant run sudo su)

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


import os
import ConfigParser
from shutil import copyfile

import app
from general import x, grep
from scopen import scOpen


def setup_permissions():
	enable_selinux()
	chmod_folders()
	chmod_files()
	find_rouge_files()
	root_console_lockdown()
	disable_virtual_terminals()
	disable_singel_user_mode()
	setup_umask()
	disable_coredumps()
	disable_su_for_wheel


def enable_selinux():
  '''
  All machines should have selinux on by default.
  For more info: http://www.crypt.gen.nz/selinux/disable_selinux.html

  '''
  app.print_verbose("Enable SELinux")
  enforcing = grep("/etc/selinux/config", "SELINUX=enforcing")
  permissive = grep("/etc/selinux/config", "SELINUX=permissive")
  if (enforcing or permissive):
    config = scOpen("/etc/selinux/config")
    config.replace('^SELINUX=.*$',     "SELINUX=enforcing")
    config.replace('^SELINUXTYPE=.*$', "SELINUXTYPE=targeted")
  else:
    app.print_error(
    	"SELinux is disabled, more need to be done, read " +
    	"http://www.crypt.gen.nz/selinux/disable_selinux.html"
    )


def chmod_folders():
	'''
	Set permissions on folders from config file.

	'''
	app.print_verbose("Set permissions on folders from config file..")
	config = ConfigParser.SafeConfigParser()
	config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)
	for setting in config.options('chmod_d'):
		name = config.get('chmod_d',setting)
		if os.path.isdir(name):
			x("chmod %s %s" % (setting, name))


def chmod_files():
	'''
	Set permissions on file from config file.

	'''
	app.print_verbose("Set permissions on file from config file..")
	config = ConfigParser.SafeConfigParser()
	config.read('%s/hardening/config.cfg' % app.SYCO_VAR_PATH)
	for setting in config.options('chmod_f'):
		name = config.get('chmod_f',setting)
		if os.path.isfile(name):
			x("chmod %s %s" % (setting, name))
			#os.chmod(fil,int(setting))
			#app.print_verbose("Setting chmod "+fil+" on file "+setting)


def find_rouge_files():
	'''
	Finds and print all file and folders that are owned by users not in the
	etc/passwd and are located in the /etc folder

	TODO: Check gid.

	'''
	app.print_verbose("Verify no rouge files.")
	#
	# Load all users from passwd
	#
	users = open("/etc/passwd")
	userlist=[]
	for line in users:
		userid = line.split(':');
		userlist.append(userid[2])

	#
	# Look for none existing users.
	#
	for dirname, dirnames, filenames in os.walk('/etc'):
		for subdirname in dirnames:
			stat_info = os.stat(os.path.join(dirname, subdirname))
			uid = stat_info.st_uid
			#gid = stat_info.st_gid
			if str(uid) not in userlist:
				app.print_verbose("  Folder %s has the strange user %s" %
					(os.path.join(dirname, subdirname), +str(uid))
				)

		for filename in filenames:
			stat_info = os.stat(os.path.join(dirname, filename))
			uid = stat_info.st_uid
			#gid = stat_info.st_gid
			if str(uid) not in userlist:
				app.print_verbose("  File %s has the strange user %s" %
					(os.path.join(dirname, filename), +str(uid))
				)


def root_console_lockdown():
	'''
	Root is only allowed to login on tty1.

	'''
	app.print_verbose("6.4 Restrict root Login to System Console")
	app.print_verbose("  Root is only allowed to login on tty1.")
	copyfile("/etc/securetty","/etc/securetty.sycobak")
	changefile = open("/etc/securetty",'w')
	changefile.write("tty1")

def disable_virtual_terminals():
  '''
  Minimize use of memory, and disable possiblity to forget a tty logged in
  when leaving the machine.

  '''
  app.print_verbose("Disable virtual terminals")
  inittab = scOpen("/etc/inittab")
  inittab.replace("^[#]?2:2345:respawn:/sbin/mingetty tty2$", "#2:2345:respawn:/sbin/mingetty tty2")
  inittab.replace("^[#]?3:2345:respawn:/sbin/mingetty tty3$", "#3:2345:respawn:/sbin/mingetty tty3")
  inittab.replace("^[#]?4:2345:respawn:/sbin/mingetty tty4$", "#4:2345:respawn:/sbin/mingetty tty4")
  inittab.replace("^[#]?5:2345:respawn:/sbin/mingetty tty5$", "#5:2345:respawn:/sbin/mingetty tty5")
  inittab.replace("^[#]?6:2345:respawn:/sbin/mingetty tty6$", "#6:2345:respawn:/sbin/mingetty tty6")


def disable_singel_user_mode():
	'''
	Disable singel user mode.

	Which let a user start the server in "recoverymode" and change password.

	'''
	app.print_verbose("Enable Authentication for Single-User Mode")
	inittab = scOpen("/etc/inittab")
	inittab.replace("^([\#]?)id:3:initdefault:",  "#id:3:initdefault:")
	inittab.replace("^~~:S:wait:/sbin/sulogin.*", "~~:S:wait:/sbin/sulogin")

	app.print_verbose("Disable Interactive Hotkey Startup at Boot")
	scOpen("/etc/sysconfig/init").replace("^PROMPT.*", "PROMPT=no")


def setup_umask():
	'''
	Set the defult dmask for all users and root. User can override this for
	private files in home folder.

	'''
	app.print_verbose("7.4 Set Default umask for Users")
	scOpen('/etc/bashrc').replace('umask 002','umask 077')
	scOpen('/etc/bashrc').replace('umask 022','umask 077')

	scOpen('/etc/profile').replace('umask 002','umask 077')
	scOpen('/etc/profile').replace('umask 022','umask 077')

	scOpen('/etc/csh.cshrc').replace('umask 002','umask 077')
	scOpen('/etc/csh.cshrc').replace('umask 022','umask 077')

	app.print_verbose("  Setup dmask for root.")
	scOpen.replace_add("/etc/skel/.bashrc", "^umask.*0777.*", "umask 0777")
	scOpen.replace_add("/root/.bashrc",     "^umask.*0777.*", "umask 0777")
	scOpen.replace_add("/root/.cshrc",      "^umask.*0777.*", "umask 0777")
	scOpen.replace_add("/root/.tcshrc",     "^umask.*0777.*", "umask 0777")


def disable_coredumps():
	'''
	Disable core dumps

	Core dump is a file with the system memory which might include password,
	credit card numbers and other sencetive information. This file is created
	when something goes wrong in the kernel.

	'''
	app.print_verbose("Disable core dumps.")
	scOpen("/etc/security/limits.conf").replace(
		"\\*.*hard.*core.*0", "* hard core 0"
	)

	scOpen("/etc/profile").replace(
		"^ulimit.*-S.*-c.*0.*>.*/dev/null.*2>&1",
		"ulimit -S -c 0 > /dev/null 2>&1"
	)

	scOpen("/etc/sysctl.conf").replace(
		"^fs.suid_dumpable.*=.*0", "fs.suid_dumpable = 0"
	)
	x("sysctl -p")


def disable_su_for_wheel():
	'''
	Disbling su fo user not in the wheel group

	'''
	app.print_verbose("Disbling su fo user not in the wheel group.")
	scOpen("/etc/pam.d/su").replace(
		"^([\#]?)auth.*required.*pam_wheel.so.*use_uid",
		"auth\t\trequired\t\tpam_wheel.so use_uid"
	)

def _clear_login_screen():
  	'''Clear information shown on the console login screen.'''
  	app.print_verbose("8.1 Set Warning Banner for Standard Login Services")
  	x('cp %s/hardening/issue.net /etc/motd' % app.SYCO_VAR_PATH)
  	x('cp %s/hardening/issue.net /etc/issue' % app.SYCO_VAR_PATH)
  	x('cp %s/hardening/issue.net /etc/issue.net' % app.SYCO_VAR_PATH)

	x("chown root:root /etc/motd")
	x("chmod 644 /etc/motd")
	x("chown root:root /etc/issue")
	x("chmod 644 /etc/issue")
	x("chown root:root /etc/issue.net")
	x("chmod 644 /etc/issue.net")

