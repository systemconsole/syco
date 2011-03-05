#!/usr/bin/env python
'''
Exceptions used in the syscon project.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

class SettingsError(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value) 
    
  def __repr__(self):
    return repr(self.value)     