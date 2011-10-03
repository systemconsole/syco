#!/usr/bin/env python
'''
Install a secure mysql server.

Read more
http://dev.mysql.com/doc/refman/5.0/en/security-guidelines.html
http://dev.mysql.com/doc/refman/5.0/en/security-against-attack.html
http://dev.mysql.com/doc/refman/5.0/en/mysqld-option-tables.html
http://www.learn-mysql-tutorial.com/SecureInstall.cfm

TODO:
* Remove the root user, only have personal sysop accounts.
* defragment_all_tables():
*   ALTER TABLE xxx ENGINE=INNODB
* calculate_cardinality():
    Unlike MyISAM, InnoDB does not store an index cardinality value in its
    tables. Instead, InnoDB computes a cardinality for a table the first time
    it accesses it after startup. With a large number of tables, this might take
    significant time. It is the initial table open operation that is important,
    so to "warm up" a table for later use, access it immediately after startup
    by issuing a statement such as SELECT 1 FROM tbl_name LIMIT 1.
* Test mysql proxy - http://dev.mysql.com/doc/refman/5.1/en/mysql-proxy.html
* Test mysql heartbeat - http://dev.mysql.com/doc/refman/5.1/en/ha-heartbeat.html
* Backup innodb??
    http://www.learn-mysql-tutorial.com/BackupRestore.cfm
    http://www.innodb.com/doc/hot_backup/manual.html
    1 Shut down your MySQL server, ensure shut down proceeds without errors.
    2 Copy all your data files (ibdata files and .ibd files) into a secure and reliable location.
    3 Copy all your ib_logfile files.
    4 Copy your configuration file(s) (my.cnf or similar).
    5 Copy all the .frm files for your InnoDB tables.

    In addition to making binary backups, you should also regularly make dumps of
    your tables with mysqldump. The reason for this is that a binary file might be
    corrupted with no visible signs. Dumped tables are stored into text files that
    are simpler and human-readable, so spotting table corruption becomes easier.
    mysqldump also has a --single- transaction option that you can use to make a
    consistent snapshot without locking out other clients.

* Need a script to check if the innodb tablespace is about to be empty.
* Investigate --chroot=name
* monitor mysql, show inodb status;
* Is binary logs properly purged
    SHOW SLAVE STATUS
    PURGE BINARY LOGS BEFORE '2008-04-02 22:46:26';
* Modify table cache
    http://dev.mysql.com/doc/refman/5.0/en/server-system-variables.html#sysvar_table_cache
    show status like '%Opened_tables%';
    shows a lot of opened files, you might like to increase table cache
* Optimization
    http://dev.mysql.com/doc/refman/5.0/en/order-by-optimization.html

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import fileinput, shutil, os
import app, general, version
import iptables

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1

def build_commands(commands):
  commands.add("install-mysql",             install_mysql, "[server-id, innodb-buffer-pool-size]", help="Install mysql server on the current server.")
  commands.add("uninstall-mysql",           uninstall_mysql,           help="Uninstall mysql server on the current server.")
  commands.add("install-mysql-replication", install_mysql_replication, help="Start repliaction from secondary master.")
  commands.add("test-mysql",                test_mysql,                help="Run all mysql unittests, to test the MySQL daemon on the current hardware.")

def install_mysql(args):
  '''
  Install and configure the mysql-server on the local host.

  '''
  app.print_verbose("Install mysql version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("InstallMysql", SCRIPT_VERSION)
  version_obj.check_executed()

  if (len(args) != 3):
    raise Exception("syco install-mysql [server-id] [innodb-buffer-pool-size]")

  server_id=args[1]
  innodb_buffer_pool_size=args[2]

  # Initialize all passwords used by the script
  app.init_mysql_passwords()

  # Install the mysql-server packages.
  if (not os.access("/usr/bin/mysqld_safe", os.W_OK|os.X_OK)):
    general.shell_exec("yum -y install mysql-server")
    general.shell_exec("/sbin/chkconfig mysqld on ")
    if (not os.access("/usr/bin/mysqld_safe", os.F_OK)):
      raise Exception("Couldn't install mysql-server")

  # Configure iptables
  iptables.add_mysql_chain()
  iptables.save()

  # Disable mysql history logging
  if (os.access("/root/.mysql_history", os.F_OK)):
    general.shell_exec("rm /root/.mysql_history")
  general.shell_exec("ln -s /dev/null /root/.mysql_history")

  # Used to log slow queries, configed in my.cnf with log-slow-queries=
  general.shell_exec("touch /var/log/mysqld-slow.log")
  general.shell_exec("chown mysql:mysql /var/log/mysqld-slow.log")
  general.shell_exec("chmod 0640 /var/log/mysqld-slow.log")
  general.shell_exec("chcon system_u:object_r:mysqld_log_t:s0 /var/log/mysqld-slow.log")

  # Not used at the moment, just preventing mysql to load any modules.
  if (not os.access("/usr/share/mysql/plugins", os.W_OK|os.X_OK)):
    os.mkdir("/usr/share/mysql/plugins")
    os.chmod("/usr/share/mysql/plugins", 0)
    os.chown("/usr/share/mysql/plugins", 0, 0)

  # Under Linux, it is advisable to disable the write-back cache. Otherwise data
  # can get lost when computer get power-failures. Beware that some drives or
  # disk controllers may be unable to disable the write-back cache.
  #
  # TODO: Might need to be done from bios?
  general.shell_exec("hdparm -W0 /dev/mapper/VolGroup00-var")

  app.print_verbose("Install /etc/my.cnf")
  shutil.copy(app.SYCO_PATH + "var/mysql/my.cnf",  "/etc/my.cnf")
  for line in fileinput.FileInput("/etc/my.cnf", inplace=1):
    line=line.replace("${server-id}", server_id)
    line=line.replace("${innodb_buffer_pool_size}", innodb_buffer_pool_size)
    print line,

  # When the innodb files are configured to be large, it takes some time to
  # generate the files.
  app.print_verbose("Increaste timeout for /etc/init.d/mysqld to 120 seconds.")
  for line in fileinput.FileInput("/etc/init.d/mysqld", inplace=1):
    line=line.replace("STARTTIMEOUT=30", "STARTTIMEOUT=120")
    print line,

  general.shell_exec("service mysqld start")

  # Secure the mysql installation.
  mysql_exec("truncate mysql.db")
  mysql_exec("truncate mysql.user")

  mysql_exec("GRANT ALL PRIVILEGES ON *.* " +
    "TO 'root'@'127.0.0.1' " + "IDENTIFIED BY '" + app.get_mysql_root_password() + "', "
    "'root'@'localhost' " + "IDENTIFIED BY '" + app.get_mysql_root_password() + "', "
    "'root'@'" + config.general.get_mysql_primary_master_ip()   + "' " + "IDENTIFIED BY '" + app.get_mysql_root_password() + "', "
    "'root'@'" + config.general.get_mysql_secondary_master_ip() + "' " + "IDENTIFIED BY '" + app.get_mysql_root_password() + "' "
    "WITH GRANT OPTION "
  )

  mysql_exec("DROP DATABASE test;")
  mysql_exec("SELECT host,user FROM mysql.user;")
  mysql_exec("RESET MASTER;")
  mysql_exec("FLUSH PRIVILEGES;")

  version_obj.mark_executed()

def uninstall_mysql(args):
  '''
  Uninstall mysql

  '''
  if (os.access("/etc/init.d/mysqld", os.F_OK)):
    general.shell_exec("/etc/init.d/mysqld stop")
  general.shell_exec("yum -y groupremove MySQL Database")
  general.shell_exec("rm -f /root/.mysql_history")
  general.shell_exec("rm -fr /usr/share/mysql")
  general.shell_exec("rm -fr /var/lib/mysql")
  general.shell_exec("rm -f /var/log/mysqld-slow.log")
  general.shell_exec("rm -f /var/log/mysqld.log.rpmsave")
  general.shell_exec("rm -f /var/log/mysqld.log")
  general.shell_exec("rm -f /etc/my.cnf")
  version_obj = version.Version("InstallMysql", SCRIPT_VERSION)
  version_obj.mark_uninstalled()

def install_mysql_replication(args):
  '''
  Setup and start the database replication in master-master mode.

  This function should be executed on the secondary master, after the
  primary master has been configured.

  '''
  app.print_verbose("Install mysql replication version: %d" % SCRIPT_VERSION)
  version_obj = version.Version("install-mysql-replication", SCRIPT_VERSION)
  version_obj.check_executed()

  general.wait_for_server_to_start(config.general.get_mysql_primary_master_ip(), "3306")

  repl_password=general.generate_password(20)

  for ip in [config.general.get_mysql_primary_master_ip(), config.general.get_mysql_secondary_master_ip()]:
    mysql_exec("stop slave;", True, ip)
    mysql_exec("delete from mysql.user where User = 'repl';", True, ip)
    mysql_exec("flush privileges;", True, ip)
    mysql_exec("GRANT REPLICATION SLAVE ON *.* TO 'repl'@'" + config.general.get_mysql_primary_master_ip() + "' IDENTIFIED BY '" + repl_password + "';", True, ip)
    mysql_exec("GRANT REPLICATION SLAVE ON *.* TO 'repl'@'" + config.general.get_mysql_secondary_master_ip() + "' IDENTIFIED BY '" + repl_password + "';", True, ip)
    if (ip==config.general.get_mysql_primary_master_ip()):
      mysql_exec("CHANGE MASTER TO MASTER_HOST='" + config.general.get_mysql_secondary_master_ip() + "', MASTER_USER='repl', MASTER_PASSWORD='" + repl_password + "'", True, ip)
    else:
      mysql_exec("CHANGE MASTER TO MASTER_HOST='" + config.general.get_mysql_primary_master_ip() + "', MASTER_USER='repl', MASTER_PASSWORD='" + repl_password + "'", True, ip)
    mysql_exec("start slave;", True, ip)

  version_obj.mark_executed()

def test_mysql(args):
  '''
  Run all mysql unittests, to test the MySQL daemon on the current hardware.

  '''
  general.shell_exec("yum -y install mysql-test")
  general.shell_exec("perl /usr/share/mysql-test/mysql-test-run.pl")
  general.shell_exec("yum -y remove mysql-test")

def mysql_exec(command, with_user=False, host="127.0.0.1"):
  '''
  Execute a MySQL query, through the command line mysql console.

  '''
  command = command.replace('\\', '\\\\')
  command = command.replace('"', r'\"')

  cmd="mysql "

  if (host):
    cmd+= "-h" + host + " "

  if (with_user):
    cmd+="-uroot -p" + app.get_mysql_root_password() + " "

  return general.shell_exec(cmd + '-e "' + command + '"')

def install_mysql_client():
  '''
  Install mysql command line client.

  '''
  general.shell_exec("yum -y install mysql.x86_64")
