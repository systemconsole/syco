#! /usr/bin/env python

import ConfigParser, subprocess, os
from socket import gethostname
from foshSsh import Ssh

class InstallServer:
  hostname = gethostname()
  verbose = True
  
  #configFileName="/opt/fareoffice/etc/install.cfg"
  configFileName="/Users/dali/Desktop/fosh/etc/install.cfg"
  
  def shellExec(self, command):
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]
    if self.verbose:
      print result
    return result  
  
  def getCommands2(self):
    config = ConfigParser.RawConfigParser()
    config.read(self.configFileName)
    
    options = []
    
    if config.has_section(self.hostname):
      for option, value in config.items(self.hostname):
        options.append([option.lower(), value])

    return sorted(options)
  
  def run2(self):
    for option, command in self.getCommands2():
      if "command" in option:
        self.shellExec(command)



  def getCommands(self, config, hostName):
    options = []
    
    if config.has_section(hostName):
      for option, value in config.items(hostName):
        options.append([option.lower(), value])

    return sorted(options)

  def run(self):
    config = ConfigParser.RawConfigParser()
    config.read(self.configFileName)  
    for hostName in config.sections():
      if not config.has_option(hostName, "server"):
        print "Error: Cant find ip for " + hostName
      else:
        server = config.get(hostName, "server")
        print "Update " + hostName + " with ip " + server
        obj = Ssh("arlukin", server)
        obj.installCert()
     
        for option, command in self.getCommands(config, hostName):
          if "command" in option:
            obj.ssh(command, verbose = True)
       
if __name__ == "__main__":
  obj = InstallServer()
  obj.run()