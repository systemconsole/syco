#!/usr/bin/env python
'''
Exeutes commands over ssh on a remote host.

Examples:
obj = Ssh("10.0.0.1", "password")
try:
  obj.install_ssh_key()
  obj.ssh_exec("uname -a")
except Exception, e:
  print("Error: " + str(e))
except SettingsError, e:
  print("Error: " + str(e))

Read more about paramiko (Currently not using paramiko)
http://jessenoller.com/2009/02/05/ssh-programming-with-paramiko-completely-different/
http://www.linuxplanet.com/linuxplanet/tutorials/6618/1/
http://www.lag.net/paramiko/docs/

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
from repr import repr
import subprocess
import sys
import pxssh, pexpect

import app
from exception import SettingsError
import general

class Ssh:

  # Remote server login data.
  server = "127.0.0.1"
  port = "22"
  user = "root"
  password = None
  mysql_password = None

  # ssh key path files. Will be stored in users home dir.
  ssh_key_dir = os.environ['HOME'] + "/.ssh"
  ssh_private_key_file = ssh_key_dir + "/id_syco_rsa"
  ssh_public_key_file = ssh_key_dir + "/id_syco_rsa.pub"

  # Cache status of installed key.
  key_is_installed = False

  # Configuration of the SSH command.
  ssh_options = "-o StrictHostKeychecking=no -o BatchMode=yes -o PasswordAuthentication=no -o GSSAPIAuthentication=no"

  def __init__(self, server, password, mysql_password=None):
    '''
    Setup the server to configure with, and with what password.

    '''
    self.server = server
    self.password = password
    self.mysql_password = mysql_password

  def install_ssh_key(self):
    '''
    Install ssh keys on a remote server.

    Raise Exception if any error.

    '''
    app.print_verbose("Install ssh key")

    self._check_alive()

    if (self._is_sshkey_installed()):
      return

    if (not os.access(self.ssh_key_dir, os.W_OK)):
      os.makedirs(self.ssh_key_dir)

    # Create ssh keys on on localhost.
    if (not os.access(self.ssh_private_key_file, os.R_OK)):
      subprocess.Popen('ssh-keygen -t rsa -f ' + self.ssh_private_key_file + ' -N ""', shell=True).communicate()

    # Get the public key.
    f = open(os.path.normpath(self.ssh_public_key_file))
    idRsaPub = f.readline().strip()

    # Install key on remote host.
    self.ssh_exec(
                  "mkdir -p .ssh;" +
                  "chmod 700 .ssh;" +
                  "touch .ssh/authorized_keys;" +
                  "chmod 640 .ssh/authorized_keys;" +
                  "echo '" + idRsaPub + "' >> .ssh/authorized_keys"
                  )

    # Raise exception if the installation of the cert failed.
    if (not self._is_sshkey_installed()):
      raise SettingsError("Failed to install cert on " + self.server)

  def is_alive(self):
    '''Is remote ssh server alive.'''
    return general.is_server_alive(self.server, self.port)

  def ssh_exec(self, command, events = {}):
    '''
    Execute the ssh command.

    Connect to the remote host, execute the command
    and closes the conneciton.

    '''
    try:
      self._ssh_exec(command, events)
    except pexpect.TIMEOUT, e:
      app.print_error("Got a timeout from ssh_exec, retry to execute command: " + command)
      self.ssh_exec(command, events)
  
  def _ssh_exec(self, command, events):
    app.print_verbose("SSH Command on " + self.server + ": " + command)

    events["Verify the SYCO master password:"] = app.get_master_password() + "\n"

    keys = events.keys()
    value = events.values()

    num_of_events = len(keys)

    # When the ssh command are executed, and back to the command prompt.
    keys.append("\[PEXPECT\]?")
    # Get return from expect() instead of exception.
    keys.append(pexpect.EOF)
    keys.append(pexpect.TIMEOUT)

    ssh = pxssh.pxssh()    
    ssh.login(self.server, username=self.user, password=self.password)
    
    app.print_verbose("---- SSH Result - Start ----", 2)
    app.print_verbose(ssh.before, 3, new_line=False)
    
    # Will duplicate output.
    #ssh.logfile_read = sys.stdout

    ssh.sendline(command)

    index=0    
    while (index < num_of_events):
      index = ssh.expect(keys)      

      app.print_verbose(ssh.before, 2, new_line=True)

      if index >= 0 and index < num_of_events:
        ssh.sendline(value[index])

    # An extra line break for the looks.
    if (app.options.verbose >= 2):      
      app.print_verbose("---- SSH Result - End-------\n", 2)

    ssh.logout()

  def mysql_exec(self, command):
    '''
    Execute a MySQL query, through the command line mysql console over SSH.

    '''
    if (not self.mysql_password):
      raise Exception("No mysql root password was defined")
    # TODO: Hide password print out.
    self.ssh_exec("mysql -uroot -p" + self.mysql_password + " -e " + '"' + command + '"')

  def rsync(self, from_path, to_path, extra=""):
    '''
    Rsync copy data from localhost to remote server.

    rsync("/tmp/foobar", "/tmp/bar")

    '''
    self.install_ssh_key()
    general.shell_exec(
                       'rsync --delete -az -e "ssh ' + self.ssh_options + " -p" + self.port + " -i " + self.ssh_private_key_file + '" ' +
                       extra + " " +
                       from_path + " " + self.user + "@" + self.server + ":" + to_path
                       )

  def _check_alive(self):
    '''Check if remote ssh server is alive, throw exception otherwise.'''
    if (not self.is_alive()):
      raise Exception(self.server + " can't be reached")

  def _is_sshkey_installed(self):
    '''Check if sshkey is installed on remote server.'''
    if (self.key_is_installed):
      return True

    p = subprocess.Popen("ssh -T " + self.ssh_options + " -i " + self.ssh_private_key_file + " " +
                         self.user + "@" + self.server + ' "uname"',
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE
                         )

    p.communicate()    

    if (p.returncode > 0):
      self.key_is_installed = False
    else:
      self.key_is_installed = True

    return self.key_is_installed

if (__name__ == "__main__"):
  app.options.verbose = 2
  obj = Ssh("localhost", "password")

  try:
    #obj.install_ssh_key()
    obj.ssh_exec("syco remote-install fo-tp-mysql-primary -v")
  except Exception, e:
    print("Error: " + str(e))
  except SettingsError, e:
    print("Error: " + str(e))
