#! /usr/bin/env python

import re, subprocess, glob, os
from socket import *  
import app

# Constants
BOLD="\033[1m"
RESET="\033[0;0m"

def remove_file(path):
  '''
  Remove file(s) in path, can use wildcard.
  remove_file('/var/log/libvirt/qemu/%s.log*')
  '''
  for file_name in glob.glob(path):
    app.print_verbose('Remove file %s' % file_name)
    os.remove('%s' % file_name)

def grep(file_name, pattern):
  '''
  Return true if regexp pattern is included in the file with 
  the name file_name
  '''
  prog = re.compile(pattern)
  for line in open(file_name):
    if prog.search(line):
      return True
  return False
  
def shell_exec(command, error=True, no_return=False):
  '''
  Execute a shell command and handles output verbosity.
  '''
  app.print_verbose("Command: " + command)
  p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  if (no_return):
    return "", ""
  else:
    return handle_subprocess(p, error)
  
def handle_subprocess(p, error=True):  
  stdout=""
  stderr=""
  while (p.poll() == None):
    for txt in p.stdout:
      # Only write caption once.
      if (stdout==""):
        app.print_verbose("---- Result ----", 2)
      app.print_verbose(txt.strip(), 2)
      stdout+=txt
      
    for txt in p.stderr:
      stderr+=txt  
          
  if (stderr and error):
    app.print_error(stderr.strip())

  if (p.returncode and error):
    app.print_error("Invalid returncode %d" % p.returncode)

  # An extra line break for the looks.
  if (stdout and app.options.verbose >=2):
    print("\n"),
            
  return stdout, stderr
  
def set_config_property(file_name, search_exp, replace_exp):
  '''Change or add a config property to a specific value'''
  if os.path.exists(file_name):
    exist=False        
    try:
      os.rename(file_name, file_name + ".bak")
      r = open(file_name + ".bak", 'r')
      w = open(file_name, 'w')
      for line in r:
        if re.search(search_exp, line):
          line = re.sub(search_exp, replace_exp, line)
          exist=True
        w.write(line)
      
      if exist == False:
        w.write(replace_exp + "\n")
    finally:
      r.close() 
      w.close() 
      os.remove(file_name + ".bak")
  else:
    w = open(file_name, 'w')
    w.write(replace_exp)
    w.close()

def is_server_alive(server, port):
  '''Check if the remote server is up and running.
  
  '''
  try:
    #app.print_verbose("Is " + server + ":" + port + " alive?", 2)
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(5)
    result = s.connect_ex((server, int(port)))   
  finally:
    s.close()
    
  if (result == 0):  
    return True
  return False  

if __name__ == "__main__":
  pass