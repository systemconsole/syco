#! /usr/bin/env python

import ConfigParser, subprocess, os, sys
import ssh, app

class RemoteInstall:  
  config_file_name=os.path.abspath(sys.path[0] + "/../etc/install.cfg") 
      
  def get_commands(self, config, host_name):
    options = []
    
    if config.has_section(host_name):
      for option, value in config.items(host_name):
        options.append([option.lower(), value])

    return sorted(options)

  def install_fosh_on_client(self, ssh):
    ssh.rsync(os.path.abspath(sys.path[0] + "/../") + "/" ,  "/opt/fosh", "--exclude version.cfg")
    ssh.ssh("/opt/fosh/bin/fosh.py install-fosh")
      
  def run(self):
    config = ConfigParser.RawConfigParser()
    config.read(self.config_file_name)  
    for host_name in config.sections():
      if not config.has_option(host_name, "server"):
        app.print_error("Cant find ip for " + host_name)
      else:
        server = config.get(host_name, "server")
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
            
            for option, command in self.get_commands(config, host_name):
              if "command" in option:
                obj.ssh(command)