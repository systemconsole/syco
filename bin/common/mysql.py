#!/usr/bin/env python
'''
Hold properties for a mysql connection needed by glassfish applications.

Example
MysqlProperties("syco", "10.0.0.2", "root", "xxxx", "syco_stable", ["127.0.0.1", "localhost"])

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

class MysqlProperties:
  pool_name=""
  jdbc_name=""
  server=""
  port=""
  user=""
  password=""
  database=""
  
  # Mysql user_specification IE. 'root'@'localhost'
  user_spec=""
  
  # Mysql user_specification with identified by IE. 'root'@'localhost' IDENTIFIED BY 'PASS'
  user_spec_identified_by=""

  # Used as a password alias in glassfish
  password_alias=""  
  
  def __init__(self, name, server, user, password, database, clients=[]):
    self.pool_name="mysql_" + name
    self.jdbc_name="jdbc/" + name
    self.server=server
    self.port=3306
    self.user=user
    self.password_alias="mysql_" + name
    self.password=password
    self.database=database
    
    for client in clients:
      if (len(self.user_spec) > 0):
        self.user_spec+=","
      self.user_spec+="'" + self.user + "'@'" + client + "'"

    for client in clients:
      if (len(self.user_spec_identified_by) > 0):
        self.user_spec_identified_by+=","
      self.user_spec_identified_by+="'" + self.user + "'@'" + client + "' IDENTIFIED BY '" + self.password + "'"
    