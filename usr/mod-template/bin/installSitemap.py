#!/usr/bin/env python
'''
Install the sitemap.fareoffice.com web page.

$ syco install-sitemap
Install sitemap.fareoffice.com into apache. Also adds a cronjob to download
updates to the sitemap in git server.

'''

__author__ = "daniel.lindh@fareoffice.com"
__copyright__ = "Copyright 2011, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel@fareoffice.com"
__credits__ = ["..."]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import time

import app
import general
import version
import ssh
import install

SYCO_FO_PATH = app.SYCO_PATH + "usr/syco-private/"

# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1

CRON_FILE = "/etc/cron.hourly/sitemap.fareoffice.com.cron"

def install_sitemap(args  ):
  app.print_verbose("Install sitemap.fareoffice.com version: %d" % SCRIPT_VERSION)

  version_obj = version.Version("InstallSitemap", SCRIPT_VERSION)
  version_obj.check_executed()

  _install_ssh_key()
  install.package("git")
  _setup_doc_apache_password()
  _config_apache()
  _setup_cron_download()
  _clone_from_git()
  _restart_httpd()

  version_obj.mark_executed()

def _install_ssh_key():
  obj = ssh.Ssh("vcs.fareoffice.com", app.get_root_password())
  obj.install_ssh_key()

def _setup_doc_apache_password():
  general.shell_exec("mkdir /etc/httpd/password")
  # youshallnotpass
  general.set_config_property2("/etc/httpd/password/htpassword", "fareoffice:H2CdK7FU5Zyx2")

def _config_apache():
  general.shell_exec("cp -f " + SYCO_FO_PATH + "var/httpd/conf.d/099-sitemap.fareoffice.com.* /etc/httpd/conf.d/")

def _setup_cron_download():
  general.shell_exec('rm -rf ' + CRON_FILE + "\n")

  w = open(CRON_FILE, 'w')

  w.write("#!/bin/bash" + "\n")
  w.write('rm -rf /var/www/html/sitemap.fareoffice.com/' + "\n")
  w.write('mkdir -p /var/www/html/sitemap.fareoffice.com/' + "\n")
  w.write('cd /var/www/html/sitemap.fareoffice.com/' + "\n")
  w.write('git clone root@vcs.fareoffice.com:/git/syco-private.git' + "\n")
  w.write('cp -R syco-private/var/httpd/html/sitemap.fareoffice.com/* .' + "\n")
  w.write('rm -rf syco-private' + "\n")
  w.write('find /var/www/html/sitemap.fareoffice.com/ -type f -exec chmod 644 {} \;' + "\n")
  w.write('find /var/www/html/sitemap.fareoffice.com/ -type d -exec chmod 755 {} \;' + "\n")
  w.write('restorecon /var/www/html/sitemap.fareoffice.com/' + "\n")

  w.close()

  general.shell_exec("chmod 755 " + CRON_FILE)
  general.shell_exec("chcon system_u:object_r:bin_t:s0 " + CRON_FILE)

def _clone_from_git():
  general.shell_exec("mkdir -P /var/www/html/")
  app.print_verbose("Download sitemap.")
  general.shell_exec(CRON_FILE)

def _restart_httpd():
  general.shell_exec("/etc/init.d/httpd restart")

if __name__ != "__main__":
  def build_commands(commands):
    commands.add("install-sitemap", install_sitemap, help="Install sitemap.fareoffice.com web page.")