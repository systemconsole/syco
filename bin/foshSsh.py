#! /usr/bin/env python

import ConfigParser, subprocess, os

class Ssh:
  user=""
  server=""
  sshKeyDir=os.environ['HOME'] + "/.ssh"
  sshPrivateKeyFile=sshKeyDir + "/id_fosh_rsa"
  sshPublicKeyFile=sshKeyDir + "/id_fosh_rsa.pub"
  verbose=False
  
  def __init__(self, user, server):
    self.user = user
    self.server = server

  def ssh(self, command, verbose = False):
    if self.verbose or verbose:
      print "SSH Execute: " + command
      
    p = subprocess.Popen("ssh -T -v -i " + self.sshPrivateKeyFile + " " + 
      self.user + "@" + self.server + ' "' + 
      command + '"', 
      shell=True, 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE
    )
    stdout, stderr = p.communicate()
    
    if self.verbose:
      print "------------- stderr"
      print stderr

    if self.verbose or verbose:        
      print "---------- stdout"
      print stdout
      print "----------"  
    
  def isCertInstalled(self):
    if self.verbose:    
      print "isCertInstalled: "
      
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
      return False
    else:
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
