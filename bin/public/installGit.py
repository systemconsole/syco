'''
Install git server software on current host.

Requires:
  syco install-httpd

Read more:
  http://whygitisbetterthanx.com/
  http://progit.org/book/
  http://www.kernel.org/pub/software/scm/git/docs/user-manual.html
  http://gitready.com/
  https://git.wiki.kernel.org/index.php/Interfaces,_frontends,_and_tools
  http://nfocipher.com/index.php?op=ViewArticle&articleId=12&blogId=1

Example:
  $ syco install-git-server  

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import shutil
import re

import app
import version
import general
import config
import ssh
from general import x
from app import INSTALL_DIR
from scopen import scOpen
import installSssd

# The version of this module, used to prevent the same script version to be 
# executed more then once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-git-server",   install_git_server, help="Install git server")

def install_git_server(args):
  app.print_verbose("Install Git-Server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallGit", SCRIPT_VERSION)
  version_obj.check_executed()

  # Get all passwords from installation user at the start of the script.
  app.get_ldap_sssd_password()
  
  x("yum -y install git")

  setup_git_user()

  setup_repo_folder()
  create_empty_test_repo()
  set_permission_on_repos()

  # Deny user git to login on SSH
  x("usermod --shell /usr/bin/git-shell git")

  install_gitweb()
  install_cgit()

  # Configure apache
  x("cp " + app.SYCO_PATH + "var/git/git.conf /etc/httpd/conf.d/git.conf")
  _install_httpd_certificates()
  _setup_ldap_auth()
  x("/etc/init.d/httpd restart")

  # Install startpage
  shutil.copy(app.SYCO_PATH + "var/git/index.html", "/var/www/html/index.html")

  version_obj.mark_executed()

def setup_git_user():
  '''
  Create linux user that should be used with "git push origin"

  '''
  x("groupadd git -g 551")
  x("adduser -m -r --shell /bin/sh -u151 -g551 git")
  x("mkdir /home/git/.ssh")
  x("touch /home/git/.ssh/authorized_keys")
  x("chown -R git:git /home/git")
  x("usermod --shell /bin/bash git")

  # Config git
  x('git config --global user.email "' + config.general.get_admin_email() + '"', user="git", cwd="/tmp")
  x('git config --global user.name "' + app.SERVER_ADMIN_NAME + '"', user="git", cwd="/tmp")

  x('git config --global user.email "' + config.general.get_admin_email() + '"')
  x('git config --global user.name "' + app.SERVER_ADMIN_NAME + '"')

def setup_repo_folder():
  '''
  Create folders where all git repos are stored.

  '''
  x("mkdir /var/lib/git")
  x("ln -s /var/lib/git /git")

def create_empty_test_repo():
  '''
  Create an empty git repo that can be used to test the git server.

  '''
  x("mkdir /var/lib/git/project.git")
  x("git --bare init --shared=group", cwd="/var/lib/git/project.git")

  # Commit README file to empty repo
  general.create_install_dir()
  x("mkdir " + INSTALL_DIR + "project")
  x("git init", cwd=INSTALL_DIR + "project")
  x("touch README", cwd=INSTALL_DIR + "project")
  x("git add README", cwd=INSTALL_DIR + "project")
  x('git commit -m"Initialized repo"', cwd=INSTALL_DIR + "project")
  x("git remote add origin file:///var/lib/git/project.git", cwd=INSTALL_DIR + "project")
  x("git push origin master", cwd=INSTALL_DIR + "project")
  x("rm -fr " + INSTALL_DIR + "project")

def set_permission_on_repos():
  '''
  Set linux and SELinux permissions on all git repos.

  '''
  x('semanage fcontext -a -t httpd_git_rw_content_t "/var/lib/git(/.*)?"')
  x("restorecon -RF /var/lib/git")
  x("chown -R git:git /var/lib/git")

def install_gitweb():
  '''
  Install the git web interface gitweb.

  '''
  x("yum -y install gitweb")  
  scOpen("/var/www/git/gitweb.cgi").replace(
    "^our.*projectroot.*", 'our $projectroot = "/var/lib/git";'
  )

def install_cgit():
  '''
  Install the git web interface cgit.

  '''
  x("yum -y install cgit")
  x("setsebool -P httpd_enable_cgi 1")  
  scOpen("/etc/cgitrc").remove("^include=.*")
  scOpen("/etc/cgitrc").add("include=/etc/cgitrepos")  
  configure_repos_for_cgit()

def configure_repos_for_cgit():
  '''
  Congigure cgit to view all installed repos.

  Note: Should be executed after new repos are added.

  '''
  x("rm -f /etc/cgitrepos")
  x("touch /etc/cgitrepos")
  
  file = scOpen("/etc/cgitrepos")
  for dir in os.listdir("/var/lib/git"):
    basename = os.path.basename(dir)
    repo_name = os.path.splitext(os.path.basename(dir))[0]
    file.add("repo.url=" + repo_name)
    file.add("repo.path=/var/lib/git/" + basename)
    file.add("repo.desc=No desc")
    file.add("repo.owner=unknown")
    file.add("")

  x("restorecon system_u:object_r:etc_t /etc/cgitrepos")
  x("rm -f /var/cache/cgit/50100000")
  x("cat /etc/cgitrepos")

def _install_httpd_certificates():
  '''
  Install syco wildcard certificate to be used by VCS server.

  Both https cert used to browse the VCS httpd server and the client certs
  used to authenticate to the LDAP-server.

  '''  
  srv = "root@" + config.general.get_cert_server_ip()

  x("mkdir -p /etc/httpd/ssl/")
  ssh.scp_from(srv, config.general.get_cert_wild_ca(), "/etc/httpd/ssl/vcs-ca.pem")
  ssh.scp_from(srv, config.general.get_cert_wild_crt(), "/etc/httpd/ssl/vcs.crt")
  ssh.scp_from(srv, config.general.get_cert_wild_key(), "/etc/httpd/ssl/vcs.key")

  installSssd.install_certs()

def _setup_ldap_auth():
  '''
  Configure the httpd conf files to authenticate against syco LDAP-server.

  '''
  fn = "/etc/httpd/conf.d/git.conf"
  scOpen(fn).replace("${AUTHLDAPBINDDN}", "cn=sssd," + config.general.get_ldap_dn())
  scOpen(fn).replace("${AUTHLDAPBINDPASSWORD}", app.get_ldap_sssd_password())

  ldapurl = "ldaps://%s:636/ou=people,%s?uid" % (
    config.general.get_ldap_hostname(),
    config.general.get_ldap_dn()
  )
  scOpen(fn).replace("${AUTHLDAPURL}", ldapurl)

  version_obj = version.Version("InstallGit", SCRIPT_VERSION)
  version_obj.mark_uninstalled()
