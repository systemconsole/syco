#! /usr/bin/env python

import subprocess, os, sys, time
from multiprocessing import Process
import ssh, app

class RemoteInstall:
  '''Run commands defined in install.cfg on remote hosts through SSH.

  If the remote host is not yet installed/started/available, 
  the script will retry to connect every 5 second until it answers.
  
  '''

  def run(self, host_name=""):
    '''Start the installation
        
    '''       
    if (host_name):
      servers = host_name
    else:    
      servers = app.get_servers()
      
    while(len(servers)):
      app.print_verbose(str(len(servers)) + " servers left to install.")
      for host_name in servers:
        if (self._execute_commands(host_name)):          
          servers.remove(host_name)
      time.sleep(5)

  def _execute_commands(self, host_name):
    '''Execute the commands on the remote host.
        
    Create one process for each remote host.    
    
    '''
    try:   
      self._validate_host_config(host_name)
  
      server = app.config.get(host_name, "server")
      app.print_verbose("Try to install " + host_name + " (" + server + ")", 2)
      obj = ssh.Ssh(server)
      if (obj.is_alive()):      
        app.print_verbose("========================================================================================")
        app.print_verbose("=== Update " + host_name + " (" + server + ")")
        app.print_verbose("========================================================================================")
  
        obj.install_cert()
        self._install_fosh_on_client(obj)
        
        p=Process(target=self._execute, args=[host_name])
        p.start()
        p.join()
        
        return True
      else:
        app.print_verbose(host_name + "(" + server + ") is not alive.", 2)
        
    except Exception, e:
      app.print_error(e.args)
      app.print_verbose("Abort installation of " + host_name)    

  def _execute(self, host_name):
    for option, command in app.get_commands(host_name):
      app.print_verbose("Execute: " + command, 2)
      obj.ssh(command)                    
        
  def _validate_host_config(self, host_name):
    '''Validate all host options in install.cfg. 
    
    Raise Exception if any errors is found.
    Print error messages in verbose mode.
       
    '''
    if (not app.config.has_option(host_name, "server")):
      app.print_error("In install.cfg, cant find ip for " + host_name)
      raise Exception()
                          
  def _install_fosh_on_client(self, ssh):
    '''Rsync fosh to remote server, and install it
    
    '''
    ssh.rsync(os.path.abspath(sys.path[0] + "/../") + "/" ,  "/opt/fosh", "--exclude version.cfg")
    ssh.ssh("/opt/fosh/bin/fosh.py install-fosh")