#! /usr/bin/env python

import ConfigParser, sys, os, socket
import app

class Version:
  hostname = socket.gethostname()
  
  command=""
  version=0
  
  config_file_name=os.path.abspath(sys.path[0] + "/../etc/version.cfg") 
  
  def __init__(self, command, version):
    self.command=command
    self.version=version
  
  def is_executed(self, command=command, version=version):
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
    
  def check_executed(self):
    '''
    Check if the command has been executed, raise Exception otherwise.
    
    '''
    if (self.is_executed(self.command, self.version)):
      raise Exception("Command " + self.command + " version " + str(self.version) + " is already executed")  

  def mark_executed(self, command="", version=""):
    '''
    Mark that a specific command/routine/script with a specific
    version has been executed on the current server.
    
    '''    
    #TODO Remove when all install scripts use mark_executed without arguments.
    if (len(command)==0):
      command=self.command
    if (len(version)==0):
      version=self.version
    
    config = ConfigParser.RawConfigParser()
    config.read(self.config_file_name)    

    if not config.has_section(self.hostname):
      config.add_section(self.hostname)
    
    config.set(self.hostname, command, version)
    configFile = open(self.config_file_name, 'wb')
    config.write(configFile)
    configFile.close()    