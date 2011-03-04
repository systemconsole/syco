#!/usr/bin/env python
'''
Exeutes commands over ssh on a remote host.

Examples:
obj = Ssh("10.0.0.1", "password")
try:
	obj.install_ssh_key()
	print(obj.ssh_exec("uname -a"))
except Exception, e:		
	print("Error: " + str(e))
except SettingsError, e:
	print("Error: " + str(e))
except paramiko.AuthenticationException, e:
	print("Error: " + str(e.args))

Read more about paramiko
http://jessenoller.com/2009/02/05/ssh-programming-with-paramiko-completely-different/
http://www.linuxplanet.com/linuxplanet/tutorials/6618/1/
http://www.lag.net/paramiko/docs/
  
Changelog:
	2011-01-29 - Daniel Lindh - Refactoring and cleaning up the code.
  2011-01-29 - Daniel Lindh - Adding file header and comments
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel.lindh@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import subprocess, os, paramiko
import app, general
from exception import SettingsError

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
    if (self._is_sshkey_installed()):
      return

    self._check_alive()
    
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
              
  def ssh_exec(self, command):
    '''
    Execute the ssh command.
    
    Connect to the remote host, execute the command 
    and closes the conneciton.
        
    '''
    app.print_verbose("SSH Command on " + self.server + ": " + command)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
    ssh.connect(self.server, username=self.user, password=self.password)
    
    stdin_file, stdout_file, stderr_file = ssh.exec_command(command)
    stdin_file.close()
    
    stdout = ""
    stderr = ""
    data = stdout_file.read().splitlines()
    for line in data:
      # Only write caption once.
      if (stdout==""):
        app.print_verbose("---- Result ----", 2)
      app.print_verbose(line, 2),
      stdout+=line
    
    data = stderr_file.read().splitlines()  
    for line in data:
      app.print_verbose(line, 2),
      stderr+=line
          
    if (stderr):
      app.print_error(stderr.strip())
        
    # An extra line break for the looks.
    if (stdout and app.options.verbose >=2):
      app.print_verbose("----------------", 2)
      print("\n"),

    return stdout, stderr
    
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
			"rsync --delete -az -e 'ssh -o StrictHostKeychecking=no -p" + self.port + " -i " + self.ssh_private_key_file + "' " + 
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

		p = subprocess.Popen("ssh -T -o StrictHostKeychecking=no -i " + self.ssh_private_key_file + " " + 
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
	obj = Ssh("10.0.0.1", "password")
	try:
		obj.install_ssh_key()
		print(obj.ssh_exec("uname -a"))
	except Exception, e:		
		print("Error: " + str(e))
	except SettingsError, e:
		print("Error: " + str(e))
	except paramiko.AuthenticationException, e:
		print("Error: " + str(e.args))
