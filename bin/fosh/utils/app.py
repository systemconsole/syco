#! /usr/bin/env python

import sys

import general
#
#  Contains global functions and settings for the fosh app
#

class Options:
  verbose=1
  
options = Options()

# The version of the fosh script
version="0.1"
parser=''

def print_error(message):
  print_verbose(general.BOLD + "Error: " + general.RESET  + message) 
    
def print_info(message):
  print_verbose("Info: " + message) 
    
def print_verbose(message):
  global options

  if (options.verbose > 0):    
    print(message)    