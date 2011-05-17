#!/usr/bin/env python
'''
Make rsnapshot backups from all syco servers to this server.

This server will connect with rsnapshot(ssh, rsync) to one and each
of the syco servers and make a backup of choosen files.

Rsnapshot will be used to save 24 copies each day, 7 copies each week, 4 copies
each month, and then one copy for each month in 12 months. Each month will
also get a .tar.gz compressed copy, that will never be removed/rotated
automatically.

All data is stored in /opt/backup. That is also the place where you should
mount your backup disk volume.

By default /etc will be backuped. If their is anything that you
don't like to backup, add that into a folder named NoBackup.

# Will be stored.
/etc/important_file.txt
# Will be ignored.
/etc/NoBackup/very_large_unimportant_file.zip

install-backup
--------------
The installation will first do all general configuration, lite rsnapshot.conf
and crontab settings. After that it will configure all alive syco servers for
backup, then it will wait until forever for the offline syco servers to become
alive. This means that crontab will start backup all servers that are alive. But
also that the offline servers will atomatically be configured for backup when
they become alive.

Configuration
-------------

install.cfg are used to specify what should be backuped.
[fo-tp-vcs]
server: 10.100.100.11
...
backup01: /var/lib/git
backup02: /var/lib/svn

You can also use that kind of setup to backup servers that are not installed
by syco. You will only need to enter server and backupXX options.

Create backup volume
--------------------

To setup the backup Volume, the following can be used, don't want to script this.
It might delete the backup volume if we run the script when we shouldn't =)

# Create the backup volume on fo-tp-vh01
vgcreate vg_backup /dev/cciss/c0d1
lvcreate -n VolBackup -l 100%FREE vg_backup
mke2fs -j /dev/vg_backup/VolBackup
mkdir /opt/backup
mount /dev/vg_backup/VolBackup /opt/backup
echo "/dev/vg_backup/VolBackup  /opt/backup  ext3  defaults  1 2" >> /etc/fstab

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import datetime
import os
import shutil
import time

import app
import general
import install
import nfs
import ssh

def build_commands(commands):
  commands.add("install-backup",   install_backup,   help="Install rsnapshot based backup server.")
  commands.add("uninstall-backup", uninstall_backup, help="Uninstall rsnapshot based backup server.")
  commands.add("tar-backup", tar_backup, help="Tar the montly copy of the backup.")

BACKUP_ROOT = "/opt/backup/rsnapshot/"

def install_backup(args):
  # Get the master password in the beginning of the script.
  # Is needed when installing the ssh key.
  app.get_master_password()

  install.package("rsnapshot")
  _configure_rsnapshot()
  _setup_cronjob()
  _setup_backup_for_all_servers()
  
def _configure_rsnapshot():
  '''
  Do the general configuration of rsnapshot

  '''
  app.print_verbose("Configure rsnapshot.")

  # Always use a default .conf file as the base.
  if (os.access("/etc/rsnapshot.conf.backup", os.F_OK)):
    shutil.copyfile("/etc/rsnapshot.conf.backup", "/etc/rsnapshot.conf")
  else:
    shutil.copyfile("/etc/rsnapshot.conf", "/etc/rsnapshot.conf.backup")

  # Set default config values.
  general.set_config_property("/etc/rsnapshot.conf", ".*snapshot_root.*", "snapshot_root\t\t" + BACKUP_ROOT)
  general.set_config_property("/etc/rsnapshot.conf", ".*cmd_ssh.*", "cmd_ssh\t\t/usr/bin/ssh")
  general.set_config_property("/etc/rsnapshot.conf", ".*interval.*hourly.*", "interval\thourly\t24")
  general.set_config_property("/etc/rsnapshot.conf", ".*interval.*monthly.*", "interval\tmonthly\t12")

  general.set_config_property("/etc/rsnapshot.conf", ".*exclude.*NoBackup.*", "exclude\tNoBackup")
  
  general.set_config_property("/etc/rsnapshot.conf", ".*backup.*etc.*localhost.*", "")
  general.set_config_property("/etc/rsnapshot.conf", ".*backup.*usr[/]local.*localhost.*", "")

def _setup_backup_for_all_servers():
  servers = app.get_servers()
  total_servers = len(servers)
  checked_servers = 0
  while(len(servers)):
    checked_servers += 1
    host_name = servers.pop()
    ip = app.get_ip(host_name)
    remote_server = ssh.Ssh(ip, app.get_root_password())
    if (remote_server.is_alive()):
      remote_server.install_ssh_key()
      _configure_backup_pathes(ip, host_name)
    else:
      servers.insert(0, host_name)      
      app.print_error("Server " + host_name + " is not alive.")

    if (checked_servers > total_servers):
      total_servers = len(servers)
      checked_servers = 0
      time.sleep(60)

def _configure_backup_pathes(ip, host_name):
  app.print_verbose("Configure rsnapshot for " + host_name + " on " + ip)

  # Add Caption
  general.set_config_property("/etc/rsnapshot.conf", "# " + host_name, "\n# " + host_name)

  for url in _get_backup_pathes(host_name):
    url = "root@" + ip + ":" + url
    new_row = "backup\t\t" + url + "\t\t" + host_name + "/"
    general.set_config_property("/etc/rsnapshot.conf", new_row, new_row)

def _get_backup_pathes(host_name):
  '''Get all pathes that should be backuped.'''
  commands = []

  # Always backup thease  
  commands.append("/etc/")

  # Backup urls from install.cfg
  if (app.config.has_section(host_name)):
    for option, value in app.config.items(host_name):
      if "backup" in option:
        commands.append(value)

  return commands

def _setup_cronjob():
  shutil.copyfile(app.SYCO_PATH + "/var/rsnapshot/crontab", "/etc/cron.d/rsnapshot")

def uninstall_backup(args):
  general.shell_exec("yum -y erase rsnapshot")
  general.shell_exec("rm /etc/cron.d/rsnapshot")
  general.shell_exec("rm /etc/rsnapshot.conf")
  general.shell_exec("rm /etc/rsnapshot.conf.backup")
  general.shell_exec("rm /etc/rsnapshot.conf.rpmsave")
  general.shell_exec("rm /var/log/rsnapshot*")

def tar_backup(args):
  '''
  Compress the montly backup for long term storage.

  It's also good with a zip backup, if one of the files on the harddrive
  get bad sectors it will otherwise be lost in all rsnapshots backups.
  Because they are the same file through hardlinks.

  '''
  YMD = str(datetime.date.today())
  
  LONGTERM_BACKUP_ROOT = BACKUP_ROOT + "longterm/" + YMD + "/"
  if (not os.access(LONGTERM_BACKUP_ROOT, os.F_OK)):
    general.shell_exec("mkdir -p " + LONGTERM_BACKUP_ROOT)

  app.print_verbose("Make a compressed backup of all folder in " + BACKUP_ROOT + "monthly.0/")
  for host_name in os.listdir(BACKUP_ROOT + "monthly.0/"):
    for folder in os.listdir(BACKUP_ROOT + "monthly.0/" + host_name):
      
      backup_name = LONGTERM_BACKUP_ROOT + host_name + "-" + folder + ".tar.gz "
      general.shell_exec(
        "tar zcf " + backup_name + " " + folder, cwd=str(BACKUP_ROOT + "monthly.0/" + host_name)
      )