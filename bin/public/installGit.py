'''
Handling git from fosh.

Read more
http://whygitisbetterthanx.com/
http://progit.org/book/
http://www.kernel.org/pub/software/scm/git/docs/user-manual.html
http://gitready.com/

https://git.wiki.kernel.org/index.php/Interfaces,_frontends,_and_tools
http://nfocipher.com/index.php?op=ViewArticle&articleId=12&blogId=1

$ fosh install-git-server
Install git server software on current host.

$ fosh git-commit "Commit comment"
Add all files in fosh folder git repo on github.

$ fosh git-clean
Remove files that should not be added to the git-repo. For now .pyc files.

Changelog:
  2011-01-28 - Daniel Lindh - Added git-clean command
  2011-01-xx - Daniel Lindh - Added git-commit command

TODO: Add commit for all plugins.
TODO: use fosh install-httpd ???
TODO: git-svn, sync with the fo svn.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The syscon project"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel@cybercow.se"
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import shutil
import re

import app
import general
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-git-server",   install_git_server, help="Install git server")
  commands.add("uninstall-git-server", uninstall_git_server, help="Uninstall git server")
  commands.add("git-commit", git_commit, "[comment]", help="Commit changes to fosh to github")
  commands.add("git-clean", git_clean, help="Remove files that should not be added to the git-repo. For now .pyc files.")

def install_git_server(args):
  app.print_verbose("Install Git-Server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallGit", SCRIPT_VERSION)
  version_obj.check_executed()

  # Install git
  general.shell_exec("yum -y install git")

  # Setup user
  general.shell_exec("groupadd git -g 551")
  general.shell_exec("adduser -m -r --shell /bin/sh -u151 -g551 git")
  general.shell_exec("mkdir /home/git/.ssh")
  general.shell_exec("touch /home/git/.ssh/authorized_keys")
  general.shell_exec("chown -R git:git /home/git")

  # Config git
  general.shell_exec('git config --global user.email "' + app.SERVER_ADMIN_EMAIL + '"', user="git")
  general.shell_exec('git config --global user.name "' + app.SERVER_ADMIN_NAME + '"', user="git")

  # Setup repo folder
  general.shell_exec("mkdir /var/lib/git")
  general.shell_exec("ln -s /var/lib/git /git")

  # Setup repo
  general.shell_exec("git clone --bare git://github.com/arlukin/fosh.git /var/lib/git/fosh.git")
  general.shell_exec("git clone --bare git://github.com/arlukin/fosh-template.git /var/lib/git/syco-private.git")

  #
  # Create an empty repo
  #
  general.shell_exec("mkdir /var/lib/git/project.git")
  general.shell_exec("git --bare init --shared=group", cwd="/var/lib/git/project.git")

  # Commit README file to empty repo
  general.create_install_dir()
  general.shell_exec("mkdir /tmp/install/project")
  general.shell_exec("git init", cwd="/tmp/install/project")
  general.shell_exec("touch README", cwd="/tmp/install/project")
  general.shell_exec("git add README", cwd="/tmp/install/project")
  general.shell_exec('git commit -m"Initialized repo"', cwd="/tmp/install/project")
  general.shell_exec("git remote add origin file:///var/lib/git/project.git", cwd="/tmp/install/project")
  general.shell_exec("git push origin master", cwd="/tmp/install/project")
  general.shell_exec("rm -fr /tmp/install/project")

  # Deny user git to login on SSH
  general.shell_exec("usermod --shell /usr/bin/git-shell git")

  # Set permission on git repos
  general.shell_exec('semanage fcontext -a -t httpd_sys_content_t "/var/lib/git(/.*)?"')
  general.shell_exec("restorecon -RF /var/lib/git")
  general.shell_exec("chown -R git:git /var/lib/git")

  # Install gitweb
  general.shell_run("yum -y install gitweb.x86_64 httpd",
    events={
      re.compile('Is this ok [(]y[/]n[)][:].*'): "y\r\n"
    }
  )
  shutil.copy(app.FOSH_PATH + "var/git/git.conf", "/etc/httpd/conf.d/git.conf")

  general.set_config_property("/var/www/git/gitweb.cgi", "^our.*projectroot.*", 'our $projectroot = "/var/lib/git";')
  #general.shell_exec("ln -s /var/lib/git /var/www/git/git")

  # Install cgit
  general.shell_exec("yum -y install cgit")
  general.shell_exec("setsebool -P httpd_enable_cgi 1")

  general.set_config_property("/etc/cgitrc", r"$include=/etc/cgitrepos", r"include=/etc/cgitrepos")

  # Configure all repos in cgit
  general.shell_exec("rm -f /etc/cgitrepos")
  general.shell_exec("touch /etc/cgitrepos")

  file = open("/etc/cgitrepos","w")
  for dir in os.listdir("/var/lib/git"):
    basename = os.path.basename(dir)
    repo_name = os.path.splitext(os.path.basename(dir))[0]
    file.write("repo.url=" + repo_name + "\n")
    file.write("repo.path=/var/lib/git/" + basename + "\n")
    file.write("repo.desc=No desc" + "\n")
    file.write("repo.owner=unknown" + "\n\n")

  general.shell_exec("chcon -R system_u:object_r:etc_t /etc/cgitrepos")
  general.shell_exec("rm -f /var/cache/cgit/50100000")
  general.shell_exec("cat /etc/cgitrepos")

  general.shell_exec("/etc/init.d/httpd restart")

  # Install startpage
  shutil.copy(app.FOSH_PATH + "var/git/index.html", "/var/www/html/index.html")

  #version_obj.mark_executed()

def uninstall_git_server(args):
  os.chdir("/tmp")
  general.shell_exec("/etc/init.d/httpd stop")
  general.shell_exec("yum -y remove git gitweb cgit perl-Git")
  general.shell_exec("rm /git")
  general.shell_exec("rm -rf /var/lib/git")
  general.shell_exec("rm /etc/cgitrepos")
  general.shell_exec("rm -rf /var/cache/cgit")
  general.shell_exec("rm -rf /home/git")
  general.shell_exec("rm -rf /var/www")
  general.shell_exec("rm -rf /etc/httpd")
  general.shell_exec("rm /root/.gitconfig")
  general.shell_exec("userdel git")

def git_commit(args):
  '''
  Commit the fosh folder to the github repository.

  '''
  comment = args[1]
  git_clean(args)
  general.shell_exec("git add *", cwd=app.FOSH_PATH)
  general.shell_exec("git commit -a -m'" + comment + "'", cwd=app.FOSH_PATH)
  general.shell_exec("git push origin", cwd=app.FOSH_PATH)

def git_clean(args):
  general.shell_exec("find " + app.FOSH_PATH + " -iname '*.pyc' -delete")