#! /usr/bin/env python

import ConfigParser, subprocess, os, paramiko

import app, general
from exception import SettingsError

class Ssh:
  '''Exeutes commands over ssh on a remote host.
  
  Read more about paramiko
  http://jessenoller.com/2009/02/05/ssh-programming-with-paramiko-completely-different/
  http://www.linuxplanet.com/linuxplanet/tutorials/6618/1/
  http://www.lag.net/paramiko/docs/
  
  '''
  server="127.0.0.1"
  port="22"  
  user="root"
  password=""

  ssh_key_dir=os.environ['HOME'] + "/.ssh"
  ssh_private_key_file=ssh_key_dir + "/id_fosh_rsa"
  ssh_public_key_file=ssh_key_dir + "/id_fosh_rsa.pub"
  key_is_installed=False
  
  def __init__(self, server, password):
    self.server=server
    self.password=password
    
  def rsync(self, from_path, to_path, extra=""):
    general.shell_exec(
      "rsync --delete -az -e 'ssh -o StrictHostKeychecking=no -p" + self.port + " -i " + self.ssh_private_key_file + "' " + 
      extra + " " +
      from_path + " " + self.user + "@" + self.server + ":" + to_path
    )  

  def ssh(self, command):
    '''
    Execute the ssh command.
    
    Connect to the remote host, execute the command 
    and closes the conneciton.    
    '''
    app.print_verbose("SSH Command: " + command)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # TODO
    # set_log_channel(self, name)    
    
    # TODO
    # Enable debug mode
    # if (app.options.verbose >=3):
    
    ssh.connect(self.server, username=self.user, password=self.password)
    
    stdin_file, stdout_file, stderr_file = ssh.exec_command(command)
    stdin_file.close()
    
    stdout=""
    stderr=""
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
         
#  def ssh_old(self, command):
#    app.print_verbose("SSH Command: " + command)
#    
#    if (app.options.verbose >=3):
#      verbose_flag="-v"
#    else:
#      verbose_flag=""
#      
#    p = subprocess.Popen("ssh -T " + verbose_flag + " -i " + self.ssh_private_key_file + " " + 
#      " -p" + self.port + " " +
#      self.user + "@" + self.server + ' "' + 
#      command + '"', 
#      shell=True, 
#      stdout=subprocess.PIPE, 
#      stderr=subprocess.PIPE
#    )
#    
#    return general.handle_subprocess(p)

  def install_cert(self):
    '''Install ssh keys on a remote server.
    
    Enables password less login.
    
    Raise Exception if any error.
    
    '''
    app.print_verbose("Install ssh key")
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
      raise SettingsError("Failed to install cert on " + self.server)

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

    env = {'SSH_ASKPASS':'/path/to/myprog', 'DISPLAY':':9999'}
    p = subprocess.Popen("ssh -T " + verbose_flag + " -i " + self.ssh_private_key_file + " " + 
      self.user + "@" + self.server + ' "uname"', 
      shell=True, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE,      
      env=env,
      preexec_fn=os.setsid
    )

    stdout,stderr=p.communicate()

    if (p.returncode > 0):
      self.key_is_installed = False
      return False
    else:
      self.key_is_installed = True
      return True