#!/usr/bin/env python
'''
Mount external server folders to localhost.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import pwd

import app
import config
from general import shell_exec
from general import shell_run
import ssh
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("mount-syco", mount_syco, "[server]", help="SSH Mount all syco servers to ~/mount/XX")
  commands.add("umount-syco", umount_syco, help="SSH Umount all syco servers on ~/mount/XX")

def mount_syco(args):
  '''
  SSH Mount all syco servers to ~/mount/XX

  Tested on Ubuntu and os x.

  '''
  app.print_verbose("Mount syco servers.")

  # Cache master password.
  app.get_root_password()

  user_name = pwd.getpwuid(os.getuid()).pw_name

  # What servers to install
  remote_host = []
  if args[1] == "":
    remote_host = config.get_servers()
  else:
    remote_host.append(args[1])

  for hostname in remote_host:
    ip = config.host(hostname).get_back_ip()
    app.print_verbose("Mount ~/mount/" + hostname + " from " + ip)
    obj = ssh.Ssh(ip, app.get_root_password())
    if (obj.is_alive()):
      obj.install_ssh_key()

      # ssh_mount_server
      mount_dir = os.environ['HOME'] + "/mount/" + hostname

      if not os.access(mount_dir, os.W_OK):
        os.makedirs(mount_dir)

      shell_run("umount " + mount_dir, user=user_name)
      sshopt = "-o StrictHostKeychecking=no -o BatchMode=yes -o PasswordAuthentication=no -o GSSAPIAuthentication=no"
      shell_run("sshfs root@" + ip + ":/opt/ " + mount_dir + " -oauto_cache,reconnect " + sshopt, user=user_name)

def umount_syco(args):
  '''
  SSH Umount all syco servers on ~/mount/XX

  Tested on Ubuntu and os x.

  '''
  app.print_verbose("Umount syco servers.")

  # Cache master password.
  app.get_root_password()

  user_name = pwd.getpwuid(os.getuid()).pw_name

  for hostname in config.get_servers():
    ip = config.host(hostname).get_back_ip()
    mount_dir = os.environ['HOME'] + "/mount/" + hostname

    if os.access(mount_dir, os.W_OK):
      shell_run("umount " + mount_dir)
