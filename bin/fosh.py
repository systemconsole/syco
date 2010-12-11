#! /usr/bin/env python

import sys, types
sys.path.append(sys.path[0] + "/fosh")
sys.path.append(sys.path[0] + "/fosh/utils")

import os, inspect
from optparse import OptionParser

import app

#  Import all py files in the fosh modules dir "fosh/bin/fosh"
for module in os.listdir(app.fosh_path + "/bin/fosh/"):
  if module == '__init__.py' or module[-3:] != '.py':
    continue
  py_command=module[:-3] + "=__import__(\"" + module[:-3] + "\", locals(), globals())"
  exec(py_command)

class Commands:
  name_list={}
  func_list={}
  arguments_list={}
  help_list={}
  
  def add(self, name, func, arguments="", help=""):
    self.name_list[name]=name.lower()
    self.func_list[name]=func
    self.arguments_list[name]=arguments
    self.help_list[name]=help

  def get_help(self):
    help=""
    name_list=sorted(self.name_list)
    for name in name_list:
      help+=(self.name_list[name] + " " + self.arguments_list[name]).ljust(25) + "- " + self.help_list[name].ljust(20) + "\n"

    return help

  def execute(self, args):
    command = args[0].lower();

    if command in self.name_list:
      self.func_list[command](args) 
    else:
      app.parser.error('Unknown command %s' % command)

# Module variables
cmd_list=Commands()
commands={}
help=""

def main():
  '''
  Used to control the command line options, and the execution of the script.
  
  First function called when using the script. 
  
  '''
  global help, cmd_list
  _init_modules()
  
  usage="usage: %prog [options] command\n"
  usage+=cmd_list.get_help()
    
  app.parser = OptionParser(usage, version="%prog " + app.version)
  app.parser.add_option("-v", "--verbose", action="store_const", const=2, dest="verbose", default=1)
  app.parser.add_option("-q", "--quiet",   action="store_const", const=0, dest="verbose")

  (app.options, args) = app.parser.parse_args()
  
  app.print_verbose(app.parser.get_version())

  if len(args) < 1 and 2 > len(args):
    app.parser.error("Incorrect number of arguments")
  else:            
    cmd_list.execute(args) 
                 
def _get_modules():
  '''
  Return a list of objects representing all available fosh modules
  
  '''
  modules=[]
  for module in os.listdir(app.fosh_path + "/bin/fosh/"):
    try:
      if module == '__init__.py' or module[-3:] != '.py':
          continue
      module=module[:-3]    
      obj = getattr(sys.modules[__name__], module)
      modules.append(obj)
      
    except NameError, e:
      app.print_error("   " + module + " is not a namespace or class")
    except AttributeError:
      raise NameError("%s doesn't exist." % module)

  return modules  
  
def _init_modules():
  '''
  Create the help and commands globals.
  
  '''
  global commands, help, cmd_list
  
  for obj in _get_modules():
    try:
      obj.build_commands(cmd_list)
                  
    except AttributeError, e:
      app.print_error("   Problem with " + repr(obj) + ", error:: " + repr(e.args))
    except NameError, e:
      app.print_error("   Problem with " + repr(obj) + ", error: " + repr(e.args))       

if __name__ == "__main__":    
  main()