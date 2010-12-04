#! /usr/bin/env python

import subprocess, os, sys
import ssh, app

class RemoteInstall:  
  def get_commands(self, host_name):
    options = []
    
    if (app.config.has_section(host_name)):
      for option, value in app.config.items(host_name):
        options.append([option.lower(), value])

    return sorted(options)

  def install_fosh_on_client(self, ssh):
    ssh.rsync(os.path.abspath(sys.path[0] + "/../") + "/" ,  "/opt/fosh", "--exclude version.cfg")
    ssh.ssh("/opt/fosh/bin/fosh.py install-fosh")

  def install_host(self, host_name):
    if (not app.config.has_option(host_name, "server")):
      app.print_error("Cant find ip for " + host_name)
    else:
      server = app.config.get(host_name, "server")
      app.print_verbose("========================================================================================")
      app.print_verbose("=== Update " + host_name + " (" + server + ")")
      app.print_verbose("========================================================================================")
      obj = ssh.Ssh(server)
      if not obj.is_alive():
        app.print_error("Client not alive")
      else:
        obj.install_cert()
        if not obj.is_cert_installed():
          app.print_error("Failed to install ssh cert.")
        else:
          self.install_fosh_on_client(obj)
          
          for option, command in self.get_commands(host_name):
            if "command" in option:
              obj.ssh(command)      

  def run(self, host_name=""):
    if (host_name):
      self.install_host(host_name)
    else:    
      for host_name in app.get_servers():
        # todo: start in new process, to install many severs 
        # simultaneous.
        self.install_host(host_name)