#! /usr/bin/env python

import subprocess, os, sys, time
from multiprocessing import Process
import ssh, app

class RemoteInstall:
  '''Run commands defined in install.cfg on remote hosts through SSH.
  
  '''

  def run(self, host_name=""):
    '''Start the installation
    
    '''
    if (host_name):
      self._execute_commands(host_name)
    else:    
      for host_name in app.get_servers():
        p=Process(target=self._execute_commands, args=[host_name])
        p.start()
      p.join()
      app.print_verbose("All hosts installed")

  def _execute_commands(self, host_name):
    '''Execute the commands on the remote host.
    
    If the remote host is not yet installed/started/available, 
    the script will retry to connect every 5 second until it answers.
    
    '''
    try:
      self._validate_host_config(host_name)
  
      server = app.config.get(host_name, "server")
      obj = ssh.Ssh(server)
      while(True):
        if (obj.is_alive()):      
          app.print_verbose("========================================================================================")
          app.print_verbose("=== Update " + host_name + " (" + server + ")")
          app.print_verbose("========================================================================================")
    
          obj.install_cert()
          self._install_fosh_on_client(obj)
          
          for option, command in app.get_commands(host_name):
            #obj.ssh(command)     
            pass
          break
        else:
          app.print_verbose(host_name + "(" + server + ") is not alive.", 2)
          time.sleep(5)
        
    except Exception, e:
      print e.args
      app.print_error(e.args)
      app.print_verbose("Abort installation of " + host_name)
        
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