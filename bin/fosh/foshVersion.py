#! /usr/bin/env python

import ConfigParser, subprocess
from socket import gethostname

class Version:
  hostname = gethostname()
  verbose = True
  
  #configFileName="/opt/fareoffice/etc/version.cfg"
  configFileName="/Users/dali/Desktop/fosh/etc/version.cfg"  
  
  def isExecuted(self, command, version):
    config = ConfigParser.RawConfigParser()
    config.read(self.configFileName)    
    
    if config.has_section(self.hostname):
      if config.has_option(self.hostname, command):
        if config.getint(self.hostname, command) >= version:
          return True
    return False

  def markExecuted(self, command, version):
    config = ConfigParser.RawConfigParser()
    config.read(self.configFileName)    

    if not config.has_section(self.hostname):
      config.add_section(self.hostname)
    
    config.set(self.hostname, command, version)
    configFile = open(self.configFileName, 'wb')
    config.write(configFile)
    configFile.close()
    
if __name__ == "__main__":
  version = Version()
  if version.isExecuted("test", 30):
    print "Already executed"
  else:
    print "Execute code"
    version.markExecuted("test", 30) 