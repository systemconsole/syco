#! /usr/bin/env python

import ConfigParser, subprocess, os
from foshSsh import Ssh

class InstallServer:
  
  #configFileName="/opt/fareoffice/etc/install.cfg"
  configFileName="/Users/dali/Desktop/fosh/etc/install.cfg"
  verbose=1
    
  def getCommands(self, config, hostName):
    options = []
    
    if config.has_section(hostName):
      for option, value in config.items(hostName):
        options.append([option.lower(), value])

    return sorted(options)

  def installFoshOnClient(self, ssh):
    if self.verbose:
      print "Install fosh client"
    ssh.rsync("/Users/dali/Desktop/fosh/",  "/opt/fosh/")
      
  def run(self):
    config = ConfigParser.RawConfigParser()
    config.read(self.configFileName)  
    for hostName in config.sections():
      if not config.has_option(hostName, "server"):
        if self.verbose:
          print "Error: Cant find ip for " + hostName
      else:
        server = config.get(hostName, "server")
        if self.verbose:
          print "Update " + hostName + " with ip " + server
        obj = Ssh("root", server)
        if not obj.isAlive():
          print "Error: Client not alive"          
        else:
          obj.installCert()
          if not obj.isCertInstalled():
            print "Error: Failed to install ssh cert."
          else:
            self.installFoshOnClient(obj)
            
            for option, command in self.getCommands(config, hostName):
              if "command" in option:
                obj.ssh(command, verbose=self.verbose+1)
       
if __name__ == "__main__":
  obj = InstallServer()
  obj.run()