#!/usr/bin/env python
'''
Install apache httpd and mod_security on current server.

Read more
http://httpd.apache.org/docs/2.2/misc/perf-tuning.html
http://www.techrepublic.com/blog/10things/10-things-you-should-do-to-secure-apache/477
http://www.petefreitag.com/item/505.cfm

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

__author__ = "matte@elino.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os

import app
import config
import general
from general import x
import version
import iptables

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

MODSEC_INSTALL_FILE = "modsecurity-2.8.0"
MODSEC_REPO_URL = "https://www.modsecurity.org/tarball/2.8.0/" + MODSEC_INSTALL_FILE + ".tar.gz"

MODSEC_MD5_FILE = MODSEC_INSTALL_FILE + ".tar.gz.sha256"
MODSEC_MD5_REPO_URL = MODSEC_REPO_URL + ".sha256"

MODSEC_RULES_FILE = "master"
MODSEC_RULES_URL = "https://github.com/SpiderLabs/owasp-modsecurity-crs/archive/{0}.zip".format(MODSEC_RULES_FILE)


def build_commands(commands):
  '''
  Defines the commands that can be executed through the syco.py shell script.

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

  iptables.add_httpd_chain()
  iptables.save()
  set_file_permissions()
  x("/etc/init.d/httpd start")

  version_obj.mark_executed()

def uninstall_httpd(args):
  '''
  Uninstal apache httpd.

  '''
  if (os.path.exists('/etc/init.d/httpd')):
    # Apache httpd
    x("yum -y erase httpd apr apr-util postgresql-libs mod_ssl distcache")

    #copy config files
    x("rm -rf /etc/httpd/")
    x("rm -rf /var/www/html")
    x("rm -r /usr/lib64/httpd/modules/mod_security2.so")

  iptables.del_httpd_chain()
  iptables.save()

  version_obj = version.Version("Installhttpd", SCRIPT_VERSION)
  version_obj.mark_uninstalled()

def set_file_permissions():
  '''
  Set file permissions on all httpd dependent folders.

  This function can be called from application installation script, to set all
  permissions after the applications apache conf files have been installed.

  '''
  x("chmod 644 /etc/httpd/conf.d/*")
  x("chcon system_u:object_r:httpd_config_t:s0 /etc/httpd/conf.d/*")

  x("chown -R root:root /etc/httpd/modsecurity.d")
  x("chmod 755 /etc/httpd/modsecurity.d")
  x("chcon -R system_u:object_r:httpd_config_t:s0 /etc/httpd/modsecurity.d")

  x("find /var/www/html/ -type f -exec chmod 644 {} \;")
  x("find /var/www/html/ -type d -exec chmod 755 {} \;")
  x("restorecon /var/www/html/")

def _install_httpd():
  # Install yum packages for apache httpd
  if (not os.path.exists('/etc/httpd/conf/httpd.conf')):
    x("yum -y install httpd mod_ssl file")
    x("/sbin/chkconfig httpd on")

  # Copy config files
  x("cp " + app.SYCO_PATH + "var/httpd/conf/httpd.conf /etc/httpd/conf/")
  x("cp " + app.SYCO_PATH + "var/httpd/conf.d/001-common.conf /etc/httpd/conf.d/")
  x("cp " + app.SYCO_PATH + "var/httpd/conf.d/002-ssl.conf /etc/httpd/conf.d/ssl.conf")

  # Secure httpd.conf
  x("sed -i 's/%s/%s/g' %s" % (
    '^ServerAdmin.*',
    'ServerAdmin ' + config.general.get_admin_email(),
    "/etc/httpd/conf/httpd.conf"
  ))

  # Remove not used files.
  x("rm -f /etc/httpd/conf.d/proxy_ajp.conf")
  x("rm -f /etc/httpd/conf.d/welcome.conf")

  # Install web pages
  x("cp -r " + app.SYCO_PATH + "var/httpd/html/* /var/www/html/")

def _install_mod_security():
  if (not os.access("/usr/lib64/httpd/modules/mod_security2.so", os.F_OK)):
    # Needed for running modsec.
    x("yum -y install pkgconfig libxml2 libxml2-devel curl lua")

    # Needed for compiling modsec
    x("yum -y install httpd-devel apr apr-util pcre make gcc pcre-devel curl-devel lua-devel")

    # Downloading and verify the pgp key for modsec.
    general.download_file(MODSEC_REPO_URL)
    general.download_file(MODSEC_MD5_REPO_URL)

    os.chdir(app.INSTALL_DIR)
    signature = x("sha256sum -c " + MODSEC_MD5_FILE)
    if (MODSEC_INSTALL_FILE + '.tar.gz: OK' not in signature):
      raise Exception("Invalid signature.")

    # Compile and install modsec
    os.chdir(app.INSTALL_DIR)
    x("tar zxf " + MODSEC_INSTALL_FILE + ".tar.gz")
    os.chdir(app.INSTALL_DIR + MODSEC_INSTALL_FILE)
    x("./configure")
    x("make")
    x("make install")
    x("chmod 755 /usr/lib64/httpd/modules/mod_security2.so")
    x("chcon system_u:object_r:httpd_modules_t:s0 /usr/lib64/httpd/modules/mod_security2.so")

    # Remove needed packages for installation of modsec.
    # TODO: See if their is any other dependencies to thease packages.
    x(
      "yum -y erase httpd-devel apr-devel apr-util-devel cpp gcc" +
      " cyrus-sasl-devel db4-devel expat-devel glibc-devel glibc-headers" +
      " kernel-headers openldap-devel pcre-devel curl-devel" +
      " lua-devel libidn-devel"
    )

  # Install mode-sec config files.
  x("cp " + app.SYCO_PATH + "var/httpd/conf.d/003-modsecurity.conf /etc/httpd/conf.d/")

def _update_modsec_rules():
  general.download_file(MODSEC_RULES_URL, MODSEC_RULES_FILE + ".zip")
  os.chdir(app.INSTALL_DIR)
  x("yum -y install unzip")
  x("rm -fR /etc/httpd/modsecurity.d")
  x("mkdir -p /etc/httpd/rules_tmp")
  x("unzip " + MODSEC_RULES_FILE + ".zip -d /etc/httpd/rules_tmp")
  x("mv /etc/httpd/rules_tmp/*/ /etc/httpd/modsecurity.d")
  x("rm -rf /etc/httpd/rules_tmp")
  x("yum -y erase unzip")

  # Install customized rules.
  x("cp " + app.SYCO_PATH + "var/httpd/modsecurity.d/* /etc/httpd/modsecurity.d")

def _enable_se_linux():
  x("/usr/sbin/setsebool -P httpd_can_network_connect=1")
