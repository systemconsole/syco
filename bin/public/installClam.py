#!/usr/bin/env python
'''
Installs clam antivirus

Read more:
  http://wiki.mattrude.com/ClamAV

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Mattias Hemingsson"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


# Path to clam installation.
CLAM_AV_URL="http://downloads.sourceforge.net/project/clamav/clamav/0.97.8/clamav-0.97.8.tar.gz?r=http%3A%2F%2Fwww.clamav.net%2Flang%2Fen%2Fdownload%2Fsources%2F&ts=1375861434&use_mirror=kent"

import app
from general import x, urlretrive
import config
from scopen import scOpen
import version


# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
  commands.add("install-clam-client", install_clam, help="Install clam antivirus.")


def install_clam(args):
  app.print_verbose("Install antivirus (clamav and freshclam).")
  version_obj = version.Version("InstallClamAntiVirus", SCRIPT_VERSION)
  version_obj.check_executed()

  prepare_installation()
  download_and_install()
  setup_clam_and_freshclam()
  setup_crontab()
  setup_autostart_and_start()

  version_obj.mark_executed()


def is_user_installed(username):
  '''
  Check if linux user is installed.

  '''
  for line in open("/etc/passwd"):
    if username in line:
      return True
  return False


def prepare_installation():
  #
  app.print_verbose("  Create user")
  if not is_user_installed("clamav"):
    x("/usr/sbin/adduser clamav -M --shell=/sbin/nologin")

  #
  app.print_verbose("Make the Pid and Socket directory")
  x("mkdir -p /var/run/clamav")
  x("chown clamav:clamav /var/run/clamav")
  x("chmod 700 /var/run/clamav")

  #
  app.print_verbose("  Create log diretories")
  x("mkdir -p /var/log/clamav")
  x("touch /var/log/clamav/freshclam.log")
  x("touch /var/log/clamav/clamd.log")

  x("chown -R clamav:clamav /var/log/clamav")
  x("chmod 700 /var/log/clamav")
  x("chmod 600 /var/log/clamav/*")

  # Create database dir
  x("mkdir -p /usr/local/share/clamav/")
  x("chown clamav:clamav /usr/local/share/clamav/")
  x("chmod 700 /usr/local/share/clamav/")


def download_and_install():
  #
  # Download and extract clamav
  #
  app.print_verbose("Download and extract clamav")
  dst_path = urlretrive(CLAM_AV_URL, "clamav_latest.tar.gz")
  x("tar -C %s -zxf %s" % (app.INSTALL_DIR, dst_path))
  compile_dir = "%scompile-clamav" % app.INSTALL_DIR
  x("mkdir -p %s" % compile_dir)
  x("mv %s/clamav-*/* %s" % (app.INSTALL_DIR, compile_dir))

  #
  # Install packages required for compiling
  #
  x("yum -y install gcc make gcc-c++ zlib-devel bzip2-devel ncurses-devel file")

  #
  # Build and install clamav and freshclam
  #
  app.print_verbose("Build and install clamav and freshclam")
  x("chown -R root:root %s" % compile_dir)
  x("./configure", cwd=compile_dir)
  x("make", cwd=compile_dir)
  x("make install", cwd=compile_dir)
  x("ldconfig")

  #
  # Remove packages needed for compilation.
  #
  x
  (
    "yum remove zlib-devel bzip2-devel ncurses-devel " +
    "gcc make cloog-ppl cpp glibc-devel glibc-headers kernel-headers "+
    "libgomp mpfr ppl gcc-c++ libstdc++-devel"
  )


def setup_clam_and_freshclam():
  #
  # Setup clamav and freshclam
  #
  app.print_verbose("Setup clamav and freshclam")

  app.print_verbose("  Setup config files.")
  clamd = scOpen("/usr/local/etc/clamd.conf")
  clamd.replace("^[#]\?Example.*",            "#Example")
  clamd.replace("^[#]\?LogFileMaxSize.*",     "LogFileMaxSize 100M")
  clamd.replace("^[#]\?LogFile.*",            "LogFile /var/log/clamav/clamd.log")
  clamd.replace("^[#]\?LogTime.*",            "LogTime yes")
  clamd.replace("^[#]\?LogSyslog.*",          "LogSyslog yes")
  clamd.replace("^[#]\?TCPSocket.*",          "TCPSocket 3310")
  clamd.replace("^[#]\?TCPAddr.*",            "TCPAddr 127.0.0.1")
  clamd.replace("^[#]\?ExcludePath.*/proc.*", "ExcludePath ^/proc")
  clamd.replace("^[#]\?ExcludePath.*/sys.*",  "ExcludePath ^/sys")
  clamd.replace("^[#]\?User.*",               "User clamav")
  clamd.replace("^[#]\?LocalSocket.*",        "LocalSocket /var/run/clamav/clamd.socket")
  clamd.replace("^[#]\?PidFile.*",            "PidFile /var/run/clamav/clamd.pid")

  freshclam = scOpen("/usr/local/etc/freshclam.conf")
  freshclam.replace("^[#]\?Example.*",        "#Example")
  freshclam.replace("^[#]\?LogFileMaxSize.*", "LogFileMaxSize 100M")
  freshclam.replace("^[#]\?LogTime.*",        "LogTime yes")
  freshclam.replace("^[#]\?LogSyslog.*",      "LogSyslog yes")
  freshclam.replace("^[#]\?DatabaseOwner.*",  "DatabaseOwner clamav")
  freshclam.replace("^[#]\?PidFile.*",        "PidFile /var/run/clamav/freshclam.pid")
  freshclam.replace("^[#]\?DatabaseMirror.*", "DatabaseMirror database.clamav.net")
  freshclam.replace("^[#]\?UpdateLogFile.*",  "UpdateLogFile /var/log/clamav/freshclam.log")


def setup_crontab():
  #
  # Setup crontab
  #
  app.print_verbose("Setup crontab")
  x("cp %s/clam/viruscan.sh /etc/cron.daily/" % app.SYCO_VAR_PATH)
  scOpen("/etc/cron.daily/viruscan.sh").replace(
    "${ADMIN_EMAIL}", config.general.get_admin_email()
  )
  x("chmod 770 /etc/cron.daily/viruscan.sh")


def setup_autostart_and_start():
  x("cp %sclam/clamd /etc/init.d/" % app.SYCO_VAR_PATH)
  x("chmod 755 /etc/init.d/clamd")
  x("/sbin/chkconfig --add clamd")
  x("/sbin/chkconfig clamd on")

  x("cp %sclam/freshclam /etc/init.d" % app.SYCO_VAR_PATH)
  x("chmod 755 /etc/init.d/freshclam")
  x("/sbin/chkconfig --add freshclam")
  x("/sbin/chkconfig freshclam on")

  #
  app.print_verbose("Download database")
  x("/usr/local/bin/freshclam")

  # Start clamd
  app.print_verbose("Start clamd")
  x("/etc/init.d/freshclam restart")
  x("/etc/init.d/clamd restart")
