#!/usr/bin/env python
'''
Control so one version of a command is only executed once on a server.

Example:
  SCRIPT_VERSION= 1
  try_
    # Mark the version of this script.
    version_obj = version.Version("installVersion", SCRIPT_VERSION)

    # Throw an exception if already executed on this host.
    version_obj.check_executed()

    # Do some code, that should only be executed once on this server.

    version_obj.mark_executed()
  except Exception, e
    print(e)

Changelog:
2011-01-30 - Daniel Lindh - Refactoring the use off class Version.
2011-01-29 - Daniel Lindh - Adding file header and comments
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel.lindh@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import ConfigParser, socket
import app

class Version:
  hostname = socket.gethostname()

  command = None
  version = None

  config_file_name = app.FOSH_ETC_PATH + "version.cfg"

  def __init__(self, command, version):
    self.command = command
    self.version = version

  def check_executed(self):
    '''
    Check if the command has been executed, raise Exception otherwise.

    '''
    if (self._is_executed(self.command, self.version)):
      raise Exception("Command " + str(self.command) + " version " + str(self.version) + " is already executed")

  def mark_executed(self):
    '''
    Mark that a specific command/routine/script with a specific
    version has been executed on the current server.

    '''
    self._set_version(self.version)

  def mark_uninstalled(self):
    '''
    Mark that a specific command/routine/script with a verion 0, which means
    that the command has not been executed on the current server.

    '''
    self._set_version(0)

  def _is_executed(self, command=command, version=version):
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

  def _set_version(self, version):
    '''
    Set version to version config file.

    '''
    config = ConfigParser.RawConfigParser()
    config.read(self.config_file_name)

    if not config.has_section(self.hostname):
      config.add_section(self.hostname)

    config.set(self.hostname, self.command, version)
    config_file = open(self.config_file_name, 'wb')
    config.write(config_file)
    config_file.close()