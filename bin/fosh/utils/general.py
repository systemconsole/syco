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
  p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  
  return handle_subprocess(p)
  
def handle_subprocess(p):  
  stdout=""
  stderr=""
  while (p.poll() == None):
    for txt in p.stdout:
      if (p.stdout and app.options.verbose >=2):
        # Only write caption once.
        if (stdout==""):
          app.print_verbose("---- Result ----")          
        print txt,  
      stdout+=txt
      
    for txt in p.stderr:
      stderr+=txt  
      
  if (stderr):
    app.print_error(stderr.strip())

  if (p.returncode):
    app.print_error("Invalid returncode %d" % p.returncode)
            
  return stdout

if __name__ == "__main__":
  pass