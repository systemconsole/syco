#! /usr/bin/env python

import ConfigParser, subprocess, os
from socket import *  

import app, general

class Ssh:
  user="root"
  server=""
  port="22"
  ssh_key_dir=os.environ['HOME'] + "/.ssh"
  ssh_private_key_file=ssh_key_dir + "/id_fosh_rsa"
  ssh_public_key_file=ssh_key_dir + "/id_fosh_rsa.pub"
  cert_is_installed=False
  
  def __init__(self, server):
    self.server = server
    
  def rsync(self, fromPath, toPath):
    general.shell_exec(
      "rsync -az -e 'ssh -p" + self.port + " -i " + self.ssh_private_key_file + "' " + 
      fromPath + " " + self.user + "@" + self.server + ":" + toPath
    )  

  def ssh(self, command):
    app.print_verbose("SSH Execute: " + command)
      
    p = subprocess.Popen("ssh -T -v -i " + self.ssh_private_key_file + " " + 
      " -p" + self.port + " " +
      self.user + "@" + self.server + ' "' + 
      command + '"', 
      shell=True, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE
    )
    stdout, stderr = p.communicate()

    if (p.returncode):
      app.print_error("Invalid returncode %d" % p.returncode)
    
    if (stdout):
      app.print_verbose("Result:")
      app.print_verbose(stdout)

    if app.options.verbose >= 1:
      app.print_error(stderr)
          
  def is_alive(self):
    s = socket(AF_INET, SOCK_STREAM)      
    result = s.connect_ex((self.server, int(self.port)))   
    s.close()
    
    if (result == 0):  
      return True
    else:
      return False    
                
  def is_cert_installed(self):      
    if self.cert_is_installed:
      return True
      
    env = {'SSH_ASKPASS':'/path/to/myprog', 'DISPLAY':':9999'}
    p = subprocess.Popen("ssh -T -v -i " + self.ssh_private_key_file + " " + 
      self.user + "@" + self.server + ' "uname"', 
      shell=True, 
      stdin=subprocess.PIPE, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE,
      env=env,
      preexec_fn=os.setsid
    )
    stdout, stderr = p.communicate()
    if  p.returncode > 0:
      if app.options.verbose >= 1:    
        app.print_error("Cert not installed. ")
        self.cert_is_installed = False
      return False
    else:
      if app.options.verbose >= 1:    
        app.print_verbose("Cert already installed. ")
        self.cert_is_installed = True
      return True
          
  def install_cert(self):
    if not os.access(self.ssh_key_dir, os.W_OK):
      os.makedirs(self.ssh_key_dir)

    if not os.access(self.ssh_private_key_file, os.R_OK):  
      subprocess.Popen('ssh-keygen -t rsa -f ' + self.ssh_private_key_file + ' -N ""', shell=True).communicate()

    if self.is_cert_installed():
      return
            
    f = open(os.path.normpath(self.ssh_public_key_file))
    idRsaPub = f.readline().strip()
    
    self.ssh(
      "mkdir -p .ssh;" +
      "chmod 700 .ssh;" +
      "touch .ssh/authorized_keys;" +
      "chmod 640 .ssh/authorized_keys;" +
      "echo '" + idRsaPub + "' >> .ssh/authorized_keys"
    )