#! /usr/bin/env python

import ConfigParser, subprocess, os
from socket import *  

class Ssh:
  user=""
  server=""
  port="22"
  sshKeyDir=os.environ['HOME'] + "/.ssh"
  sshPrivateKeyFile=sshKeyDir + "/id_fosh_rsa"
  sshPublicKeyFile=sshKeyDir + "/id_fosh_rsa.pub"
  verbose=0
  certIsInstalled=False
  
  def __init__(self, user, server):
    self.user = user
    self.server = server
    
  def shellExec(self, command):
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).communicate()[0]
    if self.verbose:
      print result
    return result      
    
  def rsync(self, fromPath, toPath):
    self.shellExec(
      "rsync -az -e 'ssh -p" + self.port + " -i " + self.sshPrivateKeyFile + "' " + 
      fromPath + " " + self.user + "@" + self.server + ":" + toPath
    )  

  def ssh(self, command, verbose = verbose):
    if verbose >= 2:
      print "----------"    
      print "SSH Execute: " + command
      
    p = subprocess.Popen("ssh -T -v -i " + self.sshPrivateKeyFile + " " + 
      " -p" + self.port + " " +
      self.user + "@" + self.server + ' "' + 
      command + '"', 
      shell=True, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE
    )
    stdout, stderr = p.communicate()
    
    if verbose >= 2:
      print stdout
      print "----------"  

    if verbose >= 3:
      print "------------- stderr"    
      print stderr
      print "-------------"
      
  def isAlive(self):
    s = socket(AF_INET, SOCK_STREAM)      
    result = s.connect_ex((self.server, int(self.port)))   
    s.close()
    
    if (result == 0):  
      return True
    else:
      return False    
                
  def isCertInstalled(self):      
    if self.certIsInstalled:
      return True
      
    env = {'SSH_ASKPASS':'/path/to/myprog', 'DISPLAY':':9999'}
    p = subprocess.Popen("ssh -T -v -i " + self.sshPrivateKeyFile + " " + 
      self.user + "@" + self.server + ' "uname"', 
      shell=True, 
      stdin=subprocess.PIPE, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE,
      env=env,
      preexec_fn=os.setsid
    )
    stdout, stderr = p.communicate()
    if  p.returncode > 0:
      if self.verbose >= 2:    
        print "Cert not installed. "
        self.certIsInstalled = False
      return False
    else:
      if self.verbose >= 2:    
        print "Cert already installed. "    
        self.certIsInstalled = True
      return True
          
  def installCert(self):
    if not os.access(self.sshKeyDir, os.W_OK):
      os.makedirs(self.sshKeyDir)

    if not os.access(self.sshPrivateKeyFile, os.R_OK):  
      subprocess.Popen('ssh-keygen -t rsa -f ' + self.sshPrivateKeyFile + ' -N ""', shell=True).communicate()

    if self.isCertInstalled():
      return
            
    f = open(os.path.normpath(self.sshPublicKeyFile))
    idRsaPub = f.readline().strip()
    
    self.ssh(
      "mkdir -p .ssh;" +
      "chmod 700 .ssh;" +
      "touch .ssh/authorized_keys;" +
      "chmod 640 .ssh/authorized_keys;" +
      "echo '" + idRsaPub + "' >> .ssh/authorized_keys"
    )

if __name__ == "__main__":
  obj = Ssh("arlukin", "192.168.0.5")
  obj.installCert()
