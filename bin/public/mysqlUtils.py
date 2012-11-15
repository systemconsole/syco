#!/usr/bin/env python
'''
Install a secure mysql server.

Read more
http://dev.mysql.com/doc/refman/5.0/en/security-guidelines.html
http://dev.mysql.com/doc/refman/5.0/en/security-against-attack.html
http://dev.mysql.com/doc/refman/5.0/en/mysqld-option-tables.html
http://www.learn-mysql-tutorial.com/SecureInstall.cfm

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
from app import print_verbose
from general import x
from installMysql import mysql_exec
import version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
SCRIPT_VERSION = 1


def build_commands(commands):
    commands.add("mysql-optimize", mysql_optimize, help="Optimize all databases and tables.")
    commands.add("mysql-check-table", mysql_check_table, help="Check table on all databases and tables.")
    commands.add("mysql-check-table-fast", mysql_check_table_fast, help="Check table fast on all databases and tables.")


def mysql_optimize(args):
    x_on_all_tables("optimize table")


def mysql_check_table(args):
    x_on_all_tables("check table")


def mysql_check_table_fast(args):
    x_on_all_tables("check table", "fast")


def x_on_all_tables(post_command, pre_command = ""):
    app.options.verbose = 1

    print_verbose("On all mysql databases execute %s %s" % (post_command, pre_command))

    app.options.verbose = 1
    databases = mysql_result("show databases")
    #databases.remove("information_schema")
    for database in databases:
        if database[0] == "information_schema":
            continue
        print_verbose("Database " + database[0])
        tables = mysql_result("show tables from " + database[0])

        width_list = [40,15,15,80]
        result = []
        for table in tables:
            result += mysql_result("%s %s.%s %s" % (post_command, database[0], table[0], pre_command))
        print_mysql_result(result, width_list)

    msg = "The batch was completed."
    print_verbose(msg)
    x("/usr/bin/logger " + msg)


def mysql_result(query):
    # Send query to mysql and get back a result.
    result = mysql_exec(query, True).strip()

    # Create row based result in a list.
    result = result.split("\n")

    # Remove column names
    result.pop(0)

    # Parse out the columns.
    result_list = []
    for row in result:
        result_list.append(row.split("\t"))

    return result_list


def print_mysql_result(result, width_list):
    for row in result:
        colcounter=0
        for col in row:
            width = width_list[colcounter]
            colcounter += 1

            print str(col).ljust(width) + " | ",
        print "\n",


def drop_user(username):
    '''
    Drop a user and its privileges.

    '''
    mysql_exec('DELETE FROM mysql.user where user="{0}";'.format(username), True)
    mysql_exec('DELETE FROM mysql.db where db="{0}";'.format(username), True)
    mysql_exec('flush privileges', True)


def create_user(username, password, database, privileges = "ALL PRIVILEGES"):
    '''
    Create a user and give it "resular" privileges.

    '''
    mysql_exec("GRANT {0} ON {1}.* TO".format(privileges, database) +
        "'{0}'@'127.0.0.1' IDENTIFIED BY '{1}', ".format(username, password) +
        "'{0}'@'localhost' IDENTIFIED BY '{1}' ".format(username, password),
        True
    )
