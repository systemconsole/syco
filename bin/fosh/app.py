#! /usr/bin/env python

import sys
#
#  Contains global functions and settings for the fosh app
#

class Options:
  verbose=1
  
options = Options()
version="0.1"
parser=''

def print_error(message):
  global parser, options

  if (options.verbose > 0):    
    app.parser.error(message) 
    
def print_info(message):
  print_verbose("Info: " + message) 
    
def print_verbose(message):
  global options

  if (options.verbose > 0):    
    print(message)    