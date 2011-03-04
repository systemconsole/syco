#!/usr/bin/env python
'''
Install apache httpd and mod_security on current server.

Read more
http://httpd.apache.org/docs/2.2/misc/perf-tuning.html
http://www.techrepublic.com/blog/10things/10-things-you-should-do-to-secure-apache/477
http://www.petefreitag.com/item/505.cfm

Changelog:
110204 - DALI - Refactoring and merging with main branch of fosh.
1101xx - MAHE - Draft of installHttpd


TODO: http://httpd.apache.org/docs/2.2/mod/directives.html
TODO: Add http://httpd.apache.org/docs/2.2/mod/mod_status.html
    disabled for best performance
    ExtendedStatus Off
TODO: Add http://httpd.apache.org/docs/2.2/mod/mod_info.html
TODO: Add http://httpd.apache.org/docs/2.2/programs/rotatelogs.html
TODO: Logrotate and other http://httpd.apache.org/docs/2.2/logs.html
TODO: Use this http://httpd.apache.org/docs/2.2/caching.html to cache static data??
TODO: Verify that http://httpd.apache.org/docs/2.2/mod/worker.html is active and not prefork.
TODO: mod_sec SecChrootDir /chroot/apache
TODO:  Read the mod_ssl User Manual for more details.
TODO: Disable DocumentRoot in httpd.conf when using virtualhost.
TODO: Add 404 page, mod_sec are redirecting to 404
TODO: When modsec fails, execute a shell script that looks for info about the attacker???

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, Fareoffice Car Rental SolutionsAB"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel@fareoffice.com"
__credits__ = ["Daniel LIndh"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

import app
import general
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

MODSEC_INSTALL_FILE = "modsecurity-apache_2.5.13"
MODSEC_REPO_URL = "http://www.modsecurity.org/download/" + MODSEC_INSTALL_FILE + ".tar.gz"

MODSEC_ASC_FILE = MODSEC_INSTALL_FILE + ".tar.gz.asc"
MODSEC_ASC_REPO_URL = MODSEC_REPO_URL + ".asc"

MODSEC_RULES_FILE = "modsecurity-crs_2.1.2"

def build_commands(commands):
  '''
  Defines the commands that can be executed through the fosh.py shell script.

  '''
  commands.add("install-httpd", install_httpd, help="Install apache webbserver on the current server.")
  commands.add("uninstall-httpd", uninstall_httpd, help="remove apache webbserver on the current server.")

def install_httpd(args):
  '''
  Apache installation

  '''
  app.print_verbose("Install Apache server version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("Installhttpd", SCRIPT_VERSION)
  version_obj.check_executed()

  _install_httpd()
  _install_mod_security()
  _update_modsec_rules()
  _enable_se_linux()

  set_file_permissions()
  general.shell_exec("/etc/init.d/httpd start")

  version_obj.mark_executed()

def set_file_permissions():
  general.shell_exec("chmod 644 /etc/httpd/conf.d/*")
  general.shell_exec("chcon system_u:object_r:httpd_config_t:s0 /etc/httpd/conf.d/*")

  general.shell_exec("chown -R root:root /etc/httpd/modsecurity.d")
  general.shell_exec("chmod 755 /etc/httpd/modsecurity.d")
  general.shell_exec("chcon -R system_u:object_r:httpd_config_t:s0 /etc/httpd/modsecurity.d")

def uninstall_httpd(args):
  '''
  Uninstal apache httpd.

  '''
  if os.path.exists('/etc/httpd/conf/httpd.conf'):
    # Apache httpd
    general.shell_exec("yum -y erase httpd apr apr-util postgresql-libs mod_ssl distcache")

    #copy config files
    general.shell_exec("rm -rf /etc/httpd/")
    general.shell_exec("rm -rf /var/www/html")
    general.shell_exec("rm -r /usr/lib64/httpd/modules/mod_security2.so")

  version_obj = version.Version("Installhttpd", SCRIPT_VERSION)
  version_obj.mark_uninstalled()
  
def _install_httpd():
  # Install yum packages for apache httpd
  if (not os.path.exists('/etc/httpd/conf/httpd.conf')):
    general.shell_exec("yum -y install httpd mod_ssl")
    general.shell_exec("chkconfig httpd on")

  # Copy config files
  general.shell_exec("cp " + app.FOSH_PATH + "var/httpd/conf/httpd.conf /etc/httpd/conf/")
  general.shell_exec("cp " + app.FOSH_PATH + "var/httpd/conf.d/001-common.conf /etc/httpd/conf.d/")
  general.shell_exec("cp " + app.FOSH_PATH + "var/httpd/conf.d/002-ssl.conf /etc/httpd/conf.d/ssl.conf")
  general.shell_exec("mv /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/002-ssl.conf")

  # Secure httpd.conf
  general.set_config_property("/etc/httpd/conf/httpd.conf", '^ServerAdmin.*', 'ServerAdmin ' + app.SERVER_ADMIN_EMAIL)

  # Remove not used files.
  general.shell_exec("rm -f /etc/httpd/conf.d/proxy_ajp.conf")
  general.shell_exec("rm -f /etc/httpd/conf.d/welcome.conf")

  # Install web pages
  general.shell_exec("cp -r " + app.FOSH_PATH + "var/httpd/html/* /var/www/html/")

def _install_mod_security():
  if (not os.access("/usr/lib64/httpd/modules/mod_security2.so", os.F_OK)):
    general.shell_exec("yum -y install httpd-devel apr apr-util pcre libxml2 make gcc pcre-devel libxml2-devel")

    # Downloading and verify the pgp key for modsec.
    general.download_file(MODSEC_REPO_URL)
    general.download_file(MODSEC_ASC_REPO_URL)

    os.chdir(app.INSTALL_DIR)
    general.shell_exec("gpg --keyserver keyserver.ubuntu.com --recv-keys 6980F8B0")
    signature = general.shell_exec("gpg --verify " + MODSEC_ASC_FILE)
    if (r'Good signature from "Breno Silva Pinto <bpinto@trustwave.com>"' not in signature):
      raise Exception("Invalid signature.")

    # Compile and install modsec
    os.chdir(app.INSTALL_DIR)
    general.shell_exec("tar zxf " + MODSEC_INSTALL_FILE + ".tar.gz")
    os.chdir(app.INSTALL_DIR + MODSEC_INSTALL_FILE + "/apache2")
    general.shell_exec("./configure")
    general.shell_exec("make")
    general.shell_exec("make install")
    general.shell_exec("chmod 755 /usr/lib64/httpd/modules/mod_security2.so")
    general.shell_exec("chcon system_u:object_r:httpd_modules_t:s0 /usr/lib64/httpd/modules/mod_security2.so")

    # Remove needed packages for installation of modsec.
    # TODO: See if their is any other dependencies to thease packages.
    general.shell_exec("yum -y erase httpd-devel apr-devel apr-util-devel "+
      "cpp gcc cyrus-sasl-devel db4-devel expat-devel glibc-devel " +
      "glibc-headers kernel-headers libgomp openldap-devel pkgconfig pcre-devel " +
      "libxml2-devel zlib-devel")

  # Install mode-sec config files.
  general.shell_exec("cp " + app.FOSH_PATH + "var/httpd/conf.d/003-modsecurity.conf /etc/httpd/conf.d/")

def _update_modsec_rules():
  general.download_file("http://sourceforge.net/projects/mod-security/files/modsecurity-crs/0-CURRENT/" + MODSEC_RULES_FILE + ".tar.gz/download", MODSEC_RULES_FILE + ".tar.gz")
  general.download_file("http://sourceforge.net/projects/mod-security/files/modsecurity-crs/0-CURRENT/" + MODSEC_RULES_FILE + ".tar.gz.asc/download", MODSEC_RULES_FILE + ".tar.gz.asc")

  os.chdir(app.INSTALL_DIR)
  general.shell_exec("gpg --keyserver keyserver.ubuntu.com --recv-keys 4EF28948")
  signature = general.shell_exec("gpg " + MODSEC_RULES_FILE + ".tar.gz.asc")
  if (r'Good signature from "Ryan Barnett (OWASP Core Rule Set Project Leader) <rbarnett@trustwave.com>"' not in signature):
    raise Exception("Invalid signature.")

  general.shell_exec("rm -fR /etc/httpd/modsecurity.d")
  general.shell_exec("tar zxvf " + MODSEC_RULES_FILE + ".tar.gz -C /etc/httpd")
  general.shell_exec("mv /etc/httpd/" + MODSEC_RULES_FILE + " /etc/httpd/modsecurity.d")

  # Install customized rules.
  general.shell_exec("cp " + app.FOSH_PATH + "var/httpd/modsecurity.d/* /etc/httpd/modsecurity.d")

def _enable_se_linux():
  general.shell_exec("/usr/sbin/setsebool httpd_can_network_connect 1")
