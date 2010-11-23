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
  
  def getCommands(self):
    config = ConfigParser.RawConfigParser()
    config.read(self.configFileName)
    
    options = []
    
    if config.has_section(self.hostname):
      for option, value in config.items(self.hostname):
        options.append([option.lower(), value])

    return sorted(options)
  
  def run(self):
    for option, command in self.getCommands():
      if "command" in option:
        self.shellExec(command)

if __name__ == "__main__":
  obj = InstallServer()
  obj.run()