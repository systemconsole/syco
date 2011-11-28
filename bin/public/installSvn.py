'''
Install subversion

Read more:
http://www.if-not-true-then-false.com/2010/install-svn-subversion-server-on-fedora-centos-red-hat-rhel/

TODO:
BACKUP??
00 23 * * * root svnadmin hotcopy /var/www/svn/fo/ /var/backup/subversion/fo
00 23 * * * root for i in $(ls /var/www/svn); do svnadmin hotcopy /var/www/svn/${i} /var/backup/subversion/${i}; done
for i in $(ls /var/www/svn); do rm -rf /var/backup/subversion/${i}.bak; mv /var/backup/subversion/${i} /var/backup/subversion/${i}.bak; svnadmin hotcopy /var/www/svn/${i} /var/backup/subversion/${i}; done

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import app
from general import x
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-svn",   install_svn, help="Install subversion")

def install_svn(args):
  app.print_verbose("Install Subversion version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallSvn", SCRIPT_VERSION)
  version_obj.check_executed()

  # Install svn
  general.shell_exec("yum -y install mod_dav_svn Subversion")

  x("/bin/cp %svar/svn/subversion.conf /etc/httpd/conf.d/subversion.conf" % app.SYCO_PATH)

  # Create repo
  x("mkdir -p /var/www/svn")
  x("ln -s /var/www/svn /svn")

  x("chown -R apache.apache /var/www/svn/")
  x("restorecon -R /var/www/svn/")
  x("service httpd restart")

  print_verbose("Use 'svnadmin create testrepo' to create a new repo")
  print_verbose("You need to edit /etc/httod/conf.d/subversion.conf.")
  version_obj.mark_executed()
