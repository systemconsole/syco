#! /usr/bin/env python

import ConfigParser, sys, os, socket
import app

class Version:
  hostname = socket.gethostname()
  
  config_file_name=os.path.abspath(sys.path[0] + "/../etc/version.cfg") 
  
  def is_executed(self, command, version):
    '''
    Check if a specific command/routine/script with a specific 
    version has been executed on the current server.
    '''
    config = ConfigParser.RawConfigParser()
    config.read(self.config_file_name)    
    
    if config.has_section(self.hostname):
      if config.has_option(self.hostname, command):
        if config.getint(self.hostname, command) >= version:
          return True
    return False

  def mark_executed(self, command, version):
    '''
    Mark that a specific command/routine/script with a specific 
    version has been executed on the current server.  
    '''
    config = ConfigParser.RawConfigParser()
    config.read(self.config_file_name)    

    if not config.has_section(self.hostname):
      config.add_section(self.hostname)
    
    config.set(self.hostname, command, version)
    configFile = open(self.config_file_name, 'wb')
    config.write(configFile)
    configFile.close()    