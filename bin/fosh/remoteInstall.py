#! /usr/bin/env python

import subprocess, os, sys, time, paramiko, getpass
from threading import Thread

import ssh, app
from exception import SettingsError

class RemoteInstall:
  '''Run commands defined in install.cfg on remote hosts through SSH.

  If the remote host is not yet installed/started/available, 
  the script will retry to connect every 5 second until it answers.
  
  '''
  
  password=""

  def run(self, host_name="", password=""):
    '''Start the installation
        
    '''       
    self.password = self._get_password()
    if (host_name):
      servers = [host_name]
    else:    
      servers = app.get_servers()
      
    while(len(servers)):
      app.print_verbose(str(len(servers)) + " servers left to install.")
      for host_name in servers:
        try:
          self._validate_host_config(host_name)
          
          if (self._execute_commands(host_name)):          
            servers.remove(host_name)
            
        except SettingsError, e:
          app.print_error(e.args)
          app.print_verbose("Abort installation of " + host_name)
          servers.remove(host_name)
          
        except paramiko.AuthenticationException, e:
          app.print_error(e.args)
          app.print_verbose("Abort installation of " + host_name)
          servers.remove(host_name)
                  
      if(len(servers)):
        time.sleep(5)

  def _execute_commands(self, host_name):
    '''Execute the commands on the remote host.
        
    Create one process for each remote host.    
    
    '''
    server = app.config.get(host_name, "server")
    app.print_verbose("Try to install " + host_name + " (" + server + ")", 2)
    obj = ssh.Ssh(server, self.password)
    if (obj.is_alive()):      
      app.print_verbose("========================================================================================")
      app.print_verbose("=== Update " + host_name + " (" + server + ")")
      app.print_verbose("========================================================================================")
      
      obj.install_cert()
      
      self._install_fosh_on_client(obj)
      
      t=Thread(target=self._execute, args=[obj, host_name])
      t.start()
      t.join()
      
      return True
    else:
      app.print_verbose(host_name + "(" + server + ") is not alive.", 2)

  def _execute(self, obj, host_name):
    for option, command in app.get_commands(host_name):
      app.print_verbose("Execute: " + command, 2)
      obj.ssh(command)                    
        
  def _validate_host_config(self, host_name):
    '''Validate all host options in install.cfg. 
    
    Raise Exception if any errors is found.
    Print error messages in verbose mode.
       
    '''
    if (not app.config.has_option(host_name, "server")):
      raise SettingsError("In install.cfg, cant find ip for " + host_name)
                          
  def _install_fosh_on_client(self, ssh):
    '''Rsync fosh to remote server, and install it
    
    '''
    app.print_verbose("Copy fosh to client")
    ssh.rsync(os.path.abspath(sys.path[0] + "/../") + "/" ,  "/opt/fosh", "--exclude version.cfg")
    ssh.rsync(os.environ['HOME'] + "/.ssh/id_rsa", os.environ['HOME'] + "/.ssh/id_rsa")
    ssh.rsync(os.environ['HOME'] + "/.ssh/id_fosh_rsa*", os.environ['HOME'] + "/.ssh/")

    ssh.ssh("/opt/fosh/bin/fosh.py install-fosh")
    
  def _get_password(self):
    while(True):
      password=getpass.getpass("Password? ")
      return password
      #confirm_password=getpass.getpass("Confirm password? ")
      #if (password==confirm_password):
      #  return password
      #else:
      #  app.print_error("Invalid password")
      
      
      
      