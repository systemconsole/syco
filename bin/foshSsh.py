#! /usr/bin/env python

import ConfigParser, subprocess, os

class Ssh:
  user="arlukin"
  server="192.168.0.5"
  sshKeyDir="/Users/dali/Desktop/fosh/var/ssh"
  sshPrivateKeyFile=sshKeyDir + "/id_rsa"
  sshPublicKeyFile=sshKeyDir + "/id_rsa.pub"
  verbose=False

  def ssh(self, command):
    if self.verbose:
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

    if self.isCertInstalled():
      return
    
    if not os.access(self.sshPrivateKeyFile, os.R_OK):  
      subprocess.Popen('ssh-keygen -t rsa -f ' + sshPrivateKeyFile + ' -N ""', shell=True).communicate()
    
    self.ssh('mkdir -p .ssh;chmod 700 .ssh;touch .ssh/authorized_keys;chmod 640 .ssh/authorized_keys')
    
    f = open(self.sshPublicKeyFile)
    idRsaPub = f.readline().strip()
    
    self.ssh('echo "' + idRsaPub + '" >> .ssh/authorized_keys')

if __name__ == "__main__":
  obj = Ssh()
  obj.installCert()
