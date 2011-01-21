#! /usr/bin/env python

#
# Install mysql server
#
# http://dev.mysql.com/doc/refman/5.0/en/security-guidelines.html
# http://dev.mysql.com/doc/refman/5.0/en/security-against-attack.html
# http://dev.mysql.com/doc/refman/5.0/en/mysqld-option-tables.html
# http://www.learn-mysql-tutorial.com/SecureInstall.cfm
#
# TODO:
# * defragment_all_tables():  
# *   ALTER TABLE xxx ENGINE=INNODB
# * calculate_cardinality():
#     Unlike MyISAM, InnoDB does not store an index cardinality value in its 
#     tables. Instead, InnoDB computes a cardinality for a table the first time 
#     it accesses it after startup. With a large number of tables, this might take 
#     significant time. It is the initial table open operation that is important, 
#     so to "warm up" a table for later use, access it immediately after startup 
#     by issuing a statement such as SELECT 1 FROM tbl_name LIMIT 1.  
# * Test mysql proxy - http://dev.mysql.com/doc/refman/5.1/en/mysql-proxy.html
# * Test mysql heartbeat - http://dev.mysql.com/doc/refman/5.1/en/ha-heartbeat.html
# * Backup innodb??
#     http://www.learn-mysql-tutorial.com/BackupRestore.cfm
#     http://www.innodb.com/doc/hot_backup/manual.html
#     1 Shut down your MySQL server, ensure shut down proceeds without errors.
#     2 Copy all your data files (ibdata files and .ibd files) into a secure and reliable location.
#     3 Copy all your ib_logfile files.
#     4 Copy your configuration file(s) (my.cnf or similar).
#     5 Copy all the .frm files for your InnoDB tables.
#   
#     In addition to making binary backups, you should also regularly make dumps of 
#     your tables with mysqldump. The reason for this is that a binary file might be
#     corrupted with no visible signs. Dumped tables are stored into text files that
#     are simpler and human-readable, so spotting table corruption becomes easier. 
#     mysqldump also has a --single- transaction option that you can use to make a 
#     consistent snapshot without locking out other clients.
# 
# * Need a script to check if the innodb tablespace is about to be empty.
# * Investigate --chroot=name
# * monitor mysql, show inodb status;
# * Is binary logs properly purged
#     SHOW SLAVE STATUS 
#     PURGE BINARY LOGS BEFORE '2008-04-02 22:46:26';
# * Modify table cache
#     http://dev.mysql.com/doc/refman/5.0/en/server-system-variables.html#sysvar_table_cache
#     show status like '%Opened_tables%';
#     shows a lot of opened files, you might like to increase table cache
# * Optimization
#     http://dev.mysql.com/doc/refman/5.0/en/order-by-optimization.html

import fileinput, shutil, os, socket
import app, general, version, net

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("install-mysql",             install_mysql,             help="Install mysql server on the current server.")  
  commands.add("uninstall-mysql",           uninstall_mysql,           help="Uninstall mysql server on the current server.")  
  commands.add("install-mysql-replication", install_mysql_replication, "[primary_master_ip]", help="Start repliaction from secondary master, fosh install_mysql_replication 10.100.100.100")
  commands.add("test-mysql",                test_mysql,                help="Run all mysql unittests, to test the MySQL daemon on the current hardware.")
    
def install_mysql(args):  
  '''
  Install and configure the mysql-server on the local host.
  
  '''
  global script_version
  app.print_verbose("Install mysql version: %d" % script_version)
  ver_obj = version.Version()
  if ver_obj.is_executed("InstallMysql", script_version):
    app.print_verbose("   Already installed latest version")
    return

  # Install the mysql-server packages.
  if (not os.access("/usr/bin/mysqld_safe", os.W_OK|os.X_OK)):      
    general.shell_exec_p("yum -y install mysql-server")
    general.shell_exec_p("chkconfig mysqld on ")

  # Disable mysql history logging
  if (os.access("/root/.mysql_history", os.F_OK)):  
    general.shell_exec_p("rm /root/.mysql_history")
  general.shell_exec_p("ln -s /dev/null /root/.mysql_history")   
  
  # Used to log slow queries, configed in my.cnf with log-slow-queries=
  general.shell_exec_p("touch /var/log/mysqld-slow.log")
  general.shell_exec_p("chown mysql:mysql /var/log/mysqld-slow.log")
  general.shell_exec_p("chmod 0640 /var/log/mysqld-slow.log")
  general.shell_exec_p("chcon system_u:object_r:mysqld_log_t:s0 /var/log/mysqld-slow.log")
  
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
  general.shell_exec_p("hdparm -W0 /dev/mapper/VolGroup00-var")
 
  app.print_verbose("Install /etc/my.cnf")
  shutil.copy("/opt/fosh/var/mysql/my.cnf",  "/etc/my.cnf")
  for line in fileinput.FileInput("/etc/my.cnf", inplace=1):
    line=line.replace("${server-id}", "1")
    line=line.replace("${innodb_buffer_pool_size}", "1G")
    print line,

  # When the innodb files are configured to be large, it takes some time to 
  # generate the files.
  app.print_verbose("Increaste timeout for /etc/init.d/mysqld to 120 seconds.")
  for line in fileinput.FileInput("/etc/init.d/mysqld", inplace=1):
    line=line.replace("STARTTIMEOUT=30", "STARTTIMEOUT=120")
    print line,

  general.shell_exec_p("service mysqld start")
  
  # Secure the mysql installation.
  mysql_exec("UPDATE mysql.user SET Password=PASSWORD('" + app.get_mysql_password() + "') WHERE user='root';")
  mysql_exec("DELETE FROM mysql.user WHERE User='root' AND Host!='localhost';")
  mysql_exec("DROP DATABASE test;")
  mysql_exec("DELETE FROM mysql.db WHERE db like 'test%';")
  mysql_exec("DELETE FROM mysql.user WHERE user = '';")
  mysql_exec("SELECT host,user FROM mysql.user;")
  mysql_exec("RESET MASTER;")  
  mysql_exec("FLUSH PRIVILEGES;")
  
  ver_obj.mark_executed("InstallMysql", script_version)  

def uninstall_mysql(args):  
  '''
  Uninstall mysql
  
  '''
  if (os.access("/etc/init.d/mysqld", os.F_OK)):
    general.shell_exec_p("/etc/init.d/mysqld stop")
  general.shell_exec_p("yum -y groupremove MySQL Database")
  general.shell_exec_p("rm -f /root/.mysql_history")
  general.shell_exec_p("rm -fr /usr/share/mysql")
  general.shell_exec_p("rm -fr /var/lib/mysql")
  general.shell_exec_p("rm -f /var/log/mysqld-slow.log")
  general.shell_exec_p("rm -f /var/log/mysqld.log.rpmsave")
  general.shell_exec_p("rm -f /var/log/mysqld.log")  
  general.shell_exec_p("rm -f /etc/my.cnf")

def install_mysql_replication(args):
  '''
  Setup and start the database replication in master-master mode.
  
  This function should be executed on the secondary master, after the
  primary master has been configured.
  
  The ip number for the primary mysql master should be eneted on the command
  line.

  Example:
  fosh install-mysql-replication 10.100.100.100
    
  '''
  if (len(args) <= 1):
    raise Exception("Error: No master database ip entered.")

  primary_master_db_ip=args[1]
  secondary_master_db_ip=net.get_lan_ip()
  repl_password=general.generate_password(20)

  mysql_exec("stop slave;", True)  
  mysql_exec("delete from mysql.user where User = 'repl';", True)
  mysql_exec("flush privileges;", True)
  mysql_exec("GRANT REPLICATION SLAVE ON *.* TO 'repl'@'" + primary_master_db_ip + "' IDENTIFIED BY '" + repl_password + "';", True)
  mysql_exec("GRANT REPLICATION SLAVE ON *.* TO 'repl'@'" + secondary_master_db_ip + "' IDENTIFIED BY '" + repl_password + "';", True)
  
  mysql_exec("CHANGE MASTER TO MASTER_HOST='" + primary_master_db_ip + "', MASTER_USER='repl', MASTER_PASSWORD='" + repl_password + "', MASTER_LOG_FILE='bin'", True)
  mysql_exec("CHANGE MASTER TO MASTER_HOST='" + primary_master_db_ip + "', MASTER_USER='repl', MASTER_PASSWORD='" + repl_password + "', MASTER_LOG_FILE='bin'", True, primary_master_db_ip)
  
  mysql_exec("start slave;", True)  
  create_databases()
  
def test_mysql(args):
  '''
  Run all mysql unittests, to test the MySQL daemon on the current hardware.
  
  '''
  general.shell_exec_p("yum -y install mysql-test")
  general.shell_exec_p("perl /usr/share/mysql-test/mysql-test-run.pl")
  general.shell_exec_p("yum -y remove mysql-test")
    
def mysql_exec(command, with_user=False, host="localhost"):
  '''
  Execute a MySQL query, through the command line mysql console.
  
  '''
  cmd="mysql "
  
  if (host):
    cmd+= "-h" + host + " "
  
  if (with_user):
    cmd+="-uroot -p" + app.get_mysql_password() + " "

  general.shell_exec_p(cmd + '-e "' + command + '"')
  
def _setup_iptables():
  pass
# *  iptables 3306
