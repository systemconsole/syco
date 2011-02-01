#!/usr/bin/env python
'''
General python functions that don't fit in it's own file.

Changelog:
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

import re
import subprocess
import glob
import os
import shutil
import string
import time
import stat

from random import choice
from socket import *  
import app

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
  
def shell_exec(command, error=True, no_return=False, user=""):
  '''
  Execute a shell command and handles output verbosity.
  '''
  
  if (user):
    command="su " + user + ' -c "' + command + '"'

  app.print_verbose("Command: " + command)
  p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  if (no_return):
    return "", ""
  else:
    return handle_subprocess(p, error)
  
def handle_subprocess(p, error=True):  
  stdout=""
  stderr=""
  while (True):
    for txt in p.stdout:
      # Only write caption once.
      if (stdout==""):
        app.print_verbose("---- Result ----", 2)
      app.print_verbose(txt.strip(), 2, new_line=False)
      stdout+=txt
      
    for txt in p.stderr:
      stderr+=txt  
  
    if (p.poll() != None):
      break
              
  if (stderr and error):
    app.print_error(stderr.strip())

  if (p.returncode and error):
    app.print_error("Invalid returncode %d" % p.returncode)

  # An extra line break for the looks.
  if (stdout and app.options.verbose >=2):
    print("\n"),
            
  return stdout, stderr
  
def shell_exec_p(command, error=True, no_return=False, user="", timeout=None, expect="", send=""):

  if (user):
    command="su " + user + ' -c "' + command + '"'

  app.print_verbose("Command: " + command)
  out = pexpect.spawn(command,
    cwd=os.getcwd()
  )
  app.print_verbose("---- Result ----", 2)
  stdout=""
  try:
    if (expect):
      while(True):
        index = out.expect ([expect, pexpect.EOF, pexpect.TIMEOUT])
        stdout+=out.before        
        app.print_verbose(out.before, 2, new_line=False)      
        if (index==0 or index==1):
          out.send(send)
          break
  
    while(True):    
      txt=out.read_nonblocking(512, timeout)
      app.print_verbose(txt, 2, new_line=False)
      stdout+=txt

  except pexpect.EOF:
    pass

  out.close()
  if (out.exitstatus and error):
    app.print_error("Invalid exitstatus %d" % out.exitstatus)

  if (out.signalstatus and error):
    app.print_error("Invalid signalstatus %d - %s" % out.signalstatus, out.status)
  
  # An extra line break for the looks.
  if (stdout and app.options.verbose >=2):
    print("\n"),
            
  return stdout

def shell_run(command, user="", events=""):

  if (user):
    command="su " + user + ' -c "' + command + '"'

  app.print_verbose("Command: " + command)
  (stdout, exit_status) = pexpect.run(command,
    cwd=os.getcwd(),
    events=events,
    withexitstatus=True,
    timeout=10000
  )

  app.print_verbose("---- Result (" + str(exit_status) + ")----", 2)
  app.print_verbose(stdout, 2)
  
  if (exit_status == None):
    raise Exception("Couldnt execute " + command)
            
  return stdout
         
def set_config_property(file_name, search_exp, replace_exp):
  '''Change or add a config property to a specific value'''
  if os.path.exists(file_name):
    exist=False        
    try:
      shutil.copyfile(file_name, file_name + ".bak")
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
  '''
  Check if the remote server is up and running.
  
  '''
  try:
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(5)
    result = s.connect_ex((server, int(port)))   
  finally:
    s.close()
    
  if (result == 0):  
    return True
  return False 
  
def wait_for_server_to_start(server, port):
  '''
  Wait until a network port is opened.
  
  '''
  app.print_verbose("Wait until " + server + " on port " + port + " starts.", new_line=False)
  while(not is_server_alive(server, port)):
    app.print_verbose(".", new_line=False)
    time.sleep(5)
  app.print_verbose(".")  
  
def generate_password(length=8, chars=string.letters + string.digits):
  return ''.join([choice(chars) for i in range(length)])        

def download_file(src, dst):
  '''
  Download a file using wget, and place in the installation tmp folder.
  
  '''
  create_install_dir()  
  os.chdir(app.INSTALL_DIR)
  if (not os.access(app.INSTALL_DIR + dst, os.F_OK)):
    shell_exec_p("wget " + src)

  if (not os.access(app.INSTALL_DIR + dst, os.F_OK)):
    raise Exception("Couldn't download: " + dst)

def create_install_dir():
  '''
  Create folder where installation files are stored during installation.
  
  '''
  if (not os.access(app.INSTALL_DIR, os.W_OK|os.X_OK)):
    os.mkdir(app.INSTALL_DIR)
    
  if (os.access(app.INSTALL_DIR, os.W_OK|os.X_OK)):
    os.chmod(app.INSTALL_DIR, stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH)
    os.chdir(app.INSTALL_DIR)
  else:
    raise Exception("Can't create install dir.")

def delete_install_dir():
  '''
  Delete the folder where installation files are stored during installation.
  
  '''
  app.print_verbose("Delete " + app.INSTALL_DIR + " used during installation.")
  shutil.rmtree(app.INSTALL_DIR, ignore_errors=True)
  pass

def install_and_import_pexpect():
  '''
  Import the pexpect module, will be installed if not already done.
  
  '''
  try:
    import pexpect
    return pexpect
  except:
    shell_exec("yum -y install pexpect")
    install_and_import_pexpect()      
    
# Import the pexpect module, will be installed if not already done.
try:
  import pexpect
except:
  shell_exec("yum -y install pexpect")
  import pexpect
    
if __name__ == "__main__":
  pass