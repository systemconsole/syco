#! /usr/bin/env python

import re, subprocess, glob
import app

# Constants
BOLD = "\033[1m"
RESET = "\033[0;0m"

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
  
def shell_exec(command):
  '''
  Execute a shell command and handles output verbosity.
  '''
  app.print_verbose("Command: " + command)
  proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
  
  result=proc.communicate()[0]
  if (proc.returncode):
    app.print_error("Invalid returncode " + int(proc.returncode))
  
  if (result):
    app.print_verbose(result)
  return result

if __name__ == "__main__":
  pass