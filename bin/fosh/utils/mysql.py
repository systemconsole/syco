#! /usr/bin/env python

class MysqlProperties:
  pool_name=""
  jdbc_name=""
  server=""
  user=""
  password=""
  database=""

  # Used as a password alias in glassfish
  password_alias=""  
  
  def __init__(self, name, server, user, password, database):
    self.pool_name="mysql_" + name
    self.jdbc_name="jdbc/" + name
    self.server=server
    self.user=user
    self.password_alias="mysql_" + name
    self.password=password
    self.database=database

def get_mysql_properties_list():
    list=[
      MysqlProperties("farepayment",           "10.100.50.1", "root", "ferdnand", "farepayment_stable"),    
      MysqlProperties("farepayment_primary",   "10.100.50.1", "root", "ferdnand", "farepayment_stable"),
      MysqlProperties("farepayment_secondary", "10.100.50.1", "root", "ferdnand", "farepayment_stable")
    ]
    return list
