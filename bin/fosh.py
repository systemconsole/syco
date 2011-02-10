#!/usr/bin/env python
'''
Main file for executing fosh commands.

fosh is a command line shell, used to execute customized installation scripts 
for linux services and softwares.

Examples:
fosh install-fosh
  
Changelog:
110210 DALI - Move private plugins from bin/private to usr/
110129 DALI - Added public and private command types, refactoring of code.
'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel.lindh@cybercow.se"
__credits__ = ["Mattias Hemmingsson"]
__license__ = "???"
__version__ = "0.1"
__status__ = "Production"

import sys, os
from optparse import OptionParser

#
# Adding file directories for inclusions.
#

# Common classes/functions that are used by the project.
sys.path.append(sys.path[0] + "/common/")

import app

# Files published to public repos.
sys.path.append(app.FOSH_PUBLIC_PATH)

#  Import all py files including fosh commands.
command_dir = os.listdir(app.FOSH_PUBLIC_PATH)

# Files only available in private user repos.
for plugin in os.listdir(app.FOSH_USR_PATH):
  plugin_path = os.path.abspath(app.FOSH_USR_PATH + "/" + plugin + "/bin/")
  sys.path.append(plugin_path)
  command_dir += os.listdir(plugin_path)

for module in command_dir:
  if (module == '__init__.py' or module[-3:] != '.py'):
    continue
  py_command = module[:-3] + "=__import__(\"" + module[:-3] + "\", locals(), globals())"
  exec(py_command)

class Commands:
  '''
  Control which command line commands that can be executed.
  
  '''

  class CommandList:
    '''
    Stores added commands for a specific type [public|private}
    
    '''
    name_list = {}
    func_list = {} 
    arguments_list = {}
    help_list = {}
        
    def __init__(self):
      self.name_list = {}
      self.func_list = {} 
      self.arguments_list = {}
      self.help_list = {}
  
  # Lists of all public and private commands
  commands = {"public":CommandList(), "private":CommandList}
  
  # The command type add() will add to.
  current_type = "public"  

  # The maximum char length of name + argument
  name_length = 0
    
  def add(self, name, func, arguments="", help=""):
    '''
    Add a command that are able to be executed from the fosh command line.
    
    This is a callback function used by the modules.
    
    '''
    self.commands[self.current_type].name_list[name] = name.lower()
    self.commands[self.current_type].func_list[name] = func
    self.commands[self.current_type].arguments_list[name] = arguments.strip("[]")
    if (self.commands[self.current_type].arguments_list[name]):
      self.commands[self.current_type].arguments_list[name] = "{" + self.commands[self.current_type].arguments_list[name] + "}"
    
    self.commands[self.current_type].help_list[name] = help.rstrip(".") + "."
    
    self.name_length = max(self.name_length, len(name))

  def execute(self, args):
    '''
    Execute a command in a module.
    
    '''
    command = args[0].lower();

    if command in self.commands["public"].name_list:
      self.commands["public"].func_list[command](args) 
    elif command in self.commands["private"].name_list:
      self.commands["private"].func_list[command](args) 
    else:
      app.parser.error('Unknown command %s' % command)

  def get_help(self):
    '''
    Get the full help text for all commands. 
    
    '''    
    help = ""
    help += "Public commands\n"
    help += self._get_help_for_command_type("public")
    help += "\nUser commands:\n"
    help += self._get_help_for_command_type("private")
    return help
    
  def _get_help_for_command_type(self, type):
    '''
    Build help string for one command type (public or private)
    
    '''
    help = ""
    name_list = sorted(self.commands[type].name_list) 
    for name in name_list:
      help += self.commands[type].name_list[name].ljust(self.name_length) + " - " 
      help += self.commands[type].help_list[name] + " " + self.commands[type].arguments_list[name] + "\n"

    return help

  def __init__(self):
    '''
    Read command directories (public and private) and add commands.
    
    '''
    try:
      self.current_type = "public"
      for obj in self._get_modules(app.FOSH_PUBLIC_PATH):
        obj.build_commands(self)

      self.current_type = "private"
      for plugin in os.listdir(app.FOSH_USR_PATH):
        plugin_path = os.path.abspath(app.FOSH_USR_PATH + "/" + plugin + "/bin/")
        for obj in self._get_modules(plugin_path):
         obj.build_commands(self)
                  
    except AttributeError, e:
      app.print_error("   Problem with " + repr(obj) + ", error:: " + repr(e.args))
    except NameError, e:
      app.print_error("   Problem with " + repr(obj) + ", error: " + repr(e.args))       
      
  def _get_modules(self, commands_path):
    '''
    Return a list of objects representing all available fosh modules in specified folder.
    
    '''
    modules=[]
    for module in os.listdir(commands_path):
      if (module == '__init__.py' or module[-3:] != '.py'):
          continue
      module = module[:-3]
      obj = getattr(sys.modules[__name__], module)
      modules.append(obj)

    return modules       

def main():
  '''
  Used to control the command line options, and the execution of the script.
  
  First function called when using the script. 
  
  '''
  # Module variables
  cmd_list = Commands()
  
  usage = "usage: %prog [options] command\n\n"
  usage += "Commands:\n"
  usage += cmd_list.get_help()
    
  app.parser = OptionParser(usage=usage, version="%prog " + app.version, add_help_option=True)
  app.parser.add_option("-v", "--verbose", action="store_const", const=2, dest="verbose", default=1, help="Show more output.")
  app.parser.add_option("-q", "--quiet",   action="store_const", const=0, dest="verbose", help="Show no output.")

  (app.options, args) = app.parser.parse_args()
  
  app.print_verbose(app.parser.get_version())

  if len(args) < 1 and 2 > len(args):
    app.parser.print_help()
  else:            
    cmd_list.execute(args) 
                 
if __name__ == "__main__":    
  main()