#!/usr/bin/env python
"""
Install a secure mariadb server.

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2017, The System Console project"
__maintainer__ = "Daniel Lindh"
__version__ = "1.0.0"
__status__ = "Production"

import fileinput
import os
import shutil

import app
import config
import general
import iptables
import net
import version
from general import x


# The version of this module, used to prevent the same script version to be
# executed more then once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    commands.add("install-mariadb", install_mariadb,
                 "[server-id, innodb-buffer-pool-size]",
                 help="Install mariadb server on the current server.")
    commands.add("uninstall-mariadb", uninstall_mariadb,
                 help="Uninstall mariadb server on the current server.")
    commands.add("install-mariadb-replication", install_mariadb_replication,
                 help="Start replication from secondary master.")
    commands.add("test-mariadb", test_mariadb,
                 help="Run all mariadb unittests, to test the MariaDB daemon on the current hardware.")


def install_mariadb(args):
    """
    Install and configure the MariaDB-server on the local host.

    """
    app.print_verbose("Install MariaDB version: %d" % SCRIPT_VERSION)
    version_obj = version.Version("InstallMariaDB", SCRIPT_VERSION)
    version_obj.check_executed()

    if len(args) != 3:
        raise Exception(
            "syco install-mariadb [server-id] [innodb-buffer-pool-size]"
        )

    # Collect command line parameters
    server_id = args[1]
    innodb_buffer_pool_size = args[2]

    # Initialize all passwords used by the script
    app.get_mysql_root_password()
    app.get_mysql_monitor_password()
    app.get_mysql_backup_password()

    # Install yum packages.
    x(
        "curl -sS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | " 
        "bash"
    )
    x("yum -y install MariaDB-server")
    x("/sbin/chkconfig mysql on")
    if not os.access("/usr/bin/mysqld_safe", os.F_OK):
        raise Exception("Couldn't install mariadb-server")

    # Configure iptables
    iptables.add_mysql_chain()
    iptables.save()

    # Disable mariadb history logging
    if os.access("/root/.mysql_history", os.F_OK):
        x("rm /root/.mysql_history")
    x("ln -s /dev/null /root/.mysql_history")

    # Used to log slow queries, configured in my.cnf with log-slow-queries=
    x("touch /var/log/mysqld-slow.log")
    x("chown mysql:mysql /var/log/mysqld-slow.log")
    x("chmod 0640 /var/log/mysqld-slow.log")
    x("chcon system_u:object_r:mysqld_log_t:s0 /var/log/mysqld-slow.log")

    app.print_verbose("Install /etc/my.cnf")
    shutil.copy(app.SYCO_PATH + "var/mariadb/my.cnf", "/etc/my.cnf.d/")
    x("chown root:root /etc/my.cnf.d/my.cnf")
    x("chmod 644 /etc/my.cnf.d/my.cnf")
    for line in fileinput.FileInput("/etc/my.cnf.d/my.cnf", inplace=1):
        line = line.replace("${server-id}", server_id)
        line = line.replace("${innodb_buffer_pool_size}",
                            innodb_buffer_pool_size)
        print line,

    x("service mysql start")

    # Secure the mysql installation.
    mysql_exec("truncate mysql.db")
    mysql_exec("truncate mysql.user")

    # Used by monitor services (icingas nrpe plugin etc.)
    mysql_exec(
        "GRANT REPLICATION CLIENT ON *.* " +
        "TO 'monitor'@'localhost' IDENTIFIED BY '%s'" % (
            app.get_mysql_monitor_password()
        )
    )
    # Required by nrpe plugins
    mysql_exec("GRANT SHOW DATABASES ON *.* TO 'monitor'@'localhost' ")

    # Used by backup scripts to flush master and check slave status etc. when
    # doing an lvm backup.
    mysql_exec(
        "GRANT RELOAD,SUPER,REPLICATION CLIENT ON *.* " +
        "TO 'backup'@'localhost' IDENTIFIED BY '%s'" % (
            app.get_mysql_backup_password()
        )
    )

    mysql_exec("DROP DATABASE test;")
    mysql_exec(
        "GRANT ALL PRIVILEGES ON *.* TO "
        "'root'@'localhost' IDENTIFIED BY '%s' "
        " WITH GRANT OPTION" % (
            app.get_mysql_root_password()
        )
    )

    # Setup Replication user
    current_host_config = config.host(net.get_hostname())
    repl_peer = current_host_config.get_option("repl_peer", 'None')
    if repl_peer and repl_peer.lower != 'none':
        mysql_exec(
            "GRANT ALL PRIVILEGES ON *.* TO "
            "'root'@'%s' IDENTIFIED BY '%s'"
            " WITH GRANT OPTION" % (
                repl_peer,
                app.get_mysql_root_password()
            )
        )

    # Flush all data
    mysql_exec("RESET MASTER")
    mysql_exec("flush privileges")

    # Display current user setttings
    app.print_verbose("Display mysql.db")
    mysql_exec("SELECT host, user FROM mysql.db", with_user=True)
    app.print_verbose("Display mysql.user")
    mysql_exec("SELECT host, user FROM mysql.user", with_user=True)

    version_obj.mark_executed()


def uninstall_mariadb(args):
    """
    Uninstall mysql

    """
    if os.access("/etc/init.d/mysql", os.F_OK):
        x("/etc/init.d/mysql stop")
    x("yum -y remove MariaDB-server")
    x("rm -f /root/.mysql_history")
    x("rm -fr /var/lib/mysql")
    x("rm -f /var/log/mysqld-slow.log")
    x("rm -f /etc/my.cnf.d")
    x("rm -f /etc/my.cnf")
    x("rm -f /etc/yum.repos.d/mariadb.repo ")

    version_obj = version.Version("InstallMariaDB", SCRIPT_VERSION)
    version_obj.mark_uninstalled()


def install_mariadb_replication(args):
    """
    Setup and start the database replication in master-master mode.

    This function should be executed on the secondary master, after the
    primary master has been configured.

    """
    app.print_verbose(
        "Install MariaDB replication version: %d" % SCRIPT_VERSION
    )
    version_obj = version.Version("install-mariadb-replication", SCRIPT_VERSION)
    version_obj.check_executed()

    current_host_config = config.host(net.get_hostname())
    repl_peer = current_host_config.get_option("repl_peer")
    general.wait_for_server_to_start(repl_peer, "3306")

    repl_password = general.generate_password(20)
    front_ip = current_host_config.get_front_ip()
    for ip in [current_host_config.get_front_ip(), repl_peer]:
        mysql_exec("stop slave;", True, ip)
        mysql_exec("delete from mysql.user where User = 'repl'", True, ip)
        mysql_exec("flush privileges;", True, ip)
        mysql_exec(
            "GRANT REPLICATION SLAVE ON *.* TO "
            "'repl'@'%s' IDENTIFIED BY '%s'," % (repl_peer, repl_password),
            "'repl'@'%s' IDENTIFIED BY '%s'" % (front_ip, repl_password),
            True, ip)

        if ip == front_ip:
            mysql_exec(
                "CHANGE MASTER TO MASTER_HOST='%s', " % repl_peer +
                "MASTER_USER='repl', MASTER_PASSWORD='%s'" % repl_password,
                True, ip
            )
        else:
            mysql_exec(
                "CHANGE MASTER TO MASTER_HOST='%s', " % front_ip +
                "MASTER_USER='repl', MASTER_PASSWORD='%s'" % repl_password,
                True, ip
            )

        mysql_exec("start slave;", True, ip)

    version_obj.mark_executed()


def test_mariadb(args):
    """
    Run all unittests for MariaDB, to test service on the current hardware.

    """
    x("yum -y install MariaDB-test")
    x("./mysql-test-run --skip-test-list=unstable-tests",
      cwd="/usr/share/mysql-test")
    # x("./mysql-stress-test.pl", cwd="/usr/share/mysql-test")
    x("yum -y remove MariaDB-test")


def mysql_exec(command, with_user=False, host="localhost", escape=True):
    """
    Execute a MySQL query, through the command line mysql console.

    todo: Don't send password on command line.

    """

    if escape:
        command = command.replace('\\', '\\\\')
        command = command.replace('"', r'\"')

    cmd = "mysql "

    if host:
        cmd += "-h" + host + " "

    if with_user:
        cmd += '-uroot -p"{0}" '.format(app.get_mysql_root_password())

    return x(cmd + '-e "{0}"'.format(command))


def install_mariadb_client():
    """
    Install Maria Db command line client.

    """
    x("yum -y install MariaDB-client")
