#! /usr/bin/env python

import ConfigParser, subprocess, os

import app, general

class Ssh:
  user="root"
  server=""
  port="22"
  ssh_key_dir=os.environ['HOME'] + "/.ssh"
  ssh_private_key_file=ssh_key_dir + "/id_fosh_rsa"
  ssh_public_key_file=ssh_key_dir + "/id_fosh_rsa.pub"
  key_is_installed=False
  
  def __init__(self, server):
    self.server = server
    
  def rsync(self, from_path, to_path, extra=""):
    general.shell_exec(
      "rsync --delete -az -e 'ssh -p" + self.port + " -i " + self.ssh_private_key_file + "' " + 
      extra + " " +
      from_path + " " + self.user + "@" + self.server + ":" + to_path
    )  

  def ssh(self, command):
    app.print_verbose("SSH Command: " + command)
    
    if (app.options.verbose >=3):
      verbose_flag="-v"
    else:
      verbose_flag=""
      
    p = subprocess.Popen("ssh -T " + verbose_flag + " -i " + self.ssh_private_key_file + " " + 
      " -p" + self.port + " " +
      self.user + "@" + self.server + ' "' + 
      command + '"', 
      shell=True, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE
    )
    
    return general.handle_subprocess(p)

  def install_cert(self):
    '''Install ssh keys on a remote server.
    
    Enables password less login.
    
    Raise Exception if any error.
    
    '''
    if (self._is_sshkey_installed()):
      return

    self._validate_alive()
    
    if (not os.access(self.ssh_key_dir, os.W_OK)):
      os.makedirs(self.ssh_key_dir)

    if (not os.access(self.ssh_private_key_file, os.R_OK)):
      subprocess.Popen('ssh-keygen -t rsa -f ' + self.ssh_private_key_file + ' -N ""', shell=True).communicate()
            
    f = open(os.path.normpath(self.ssh_public_key_file))
    idRsaPub = f.readline().strip()
    
    self.ssh(
      "mkdir -p .ssh;" +
      "chmod 700 .ssh;" +
      "touch .ssh/authorized_keys;" +
      "chmod 640 .ssh/authorized_keys;" +
      "echo '" + idRsaPub + "' >> .ssh/authorized_keys"
    )
    
    if (not self._is_sshkey_installed()):
      raise Exception("Failed to install cert on " + self.server)

  def is_alive(self):
    return general.is_server_alive(self.server, self.port)
              
  def _validate_alive(self):
    if (not self.is_alive()):  
      raise Exception(self.server + " can't be reached")
                
  def _is_sshkey_installed(self):      
    '''Check if sshkey is installed on remote server.
    
    '''
    if self.key_is_installed:
      return True

    if (app.options.verbose >=3):
      verbose_flag="-v"
    else:
      verbose_flag=""
      
    p = subprocess.Popen("ssh -T " + verbose_flag + " -i " + self.ssh_private_key_file + " " + 
      self.user + "@" + self.server + ' "uname"', 
      shell=True
    )
    
    p.communicate()
    if (p.returncode > 0):
      self.key_is_installed = False
      return False
    else:
      self.key_is_installed = True
      return True
          