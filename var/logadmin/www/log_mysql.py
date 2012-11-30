

__version__ = "0.0.1"
__status__ = "Production"


# sudo yum install MySQL-python


import MySQLdb
import sys
import os
from datetime import date, timedelta

'''
MYSQL 
'''
mysqlhost="localhost"
mysqluser="logadmin"
mysqlpass="${MYSQL_PASSWORD}"
mysqldb="Syslog"




def search_logs(when):
	'''
	Search in Syslog data
	'''

	sql ="SELECT v.* from view_SystemEvents_compact v LEFT JOIN Exclude e ON (v.Message LIKE concat('%',e.exclude,'%')) WHERE e.exclude IS NULL AND v.DeviceReportedTime BETWEEN '{0} 00:00:00' AND '{0} 23:59:59'".format(when)
	return mysql_query(sql)


def logs_are_signed(when):
	'''
	Is logs signed ?
	'''
	try:
		con = None
		con = MySQLdb.Connection(mysqlhost, mysqluser, 
								mysqlpass, mysqldb)
  		curs = con.cursor()
  		curs.execute("SELECT sign FROM signed WHERE date = '{0}'".format(when))
  		
		
		row = curs.fetchone()	
		if not row:
			return "Not Signed"
		else:
			return row[0]
        #x("logger -t syco -p user.info LogToEmail run sql query %s" % result.fetch_row()[0])

	except MySQLdb.Error, e:
		print "Error in LogToEmail {0} : {1}".format(e.args[0], e.args[1])
		sys.exit(1)
	finally:
		if con:
			con.close()


def sign_logs(time,user,mess,now):
	'''
	Sign the logs file by date
	'''
	sql="INSERT INTO signed(date,sign,mess,signdate) VALUES ('{0}','{1}','{2}','{3}')".format(time,user,mess,now)
	mysql_query(sql)
	

def get_signed():
	'''
	Get all logs that are signed
	'''
	sql="SELECT date,sign,signdate FROM signed"
	return mysql_query(sql)

def get_loghosts():
	'''
	Get all logs that are signed
	'''
	sql="select distinct(FromHost) AS FromHost FROM view_SystemEvents_host_sum;"
	return mysql_query(sql)

def get_exclude():
	'''
	Returns an list with excluded objects
	'''
	sql="SELECT exclude,user,adddate,id,status FROM Exclude ORDER BY id DESC;"
	return mysql_query(sql)

def del_exclude(id):
	'''
	Deleting excludning record
	'''
	sql="delete from Exclude where id ='{0}'".format(id)
	mysql_query(sql)

def add_exclude(ex_this,status):
	'''
	Exclude this from logs
	'''
	sql="INSERT INTO Exclude(exclude,user,adddate,status) VALUES('{0}','{1}','{2}','{3}')".format(ex_this,os.environ["REMOTE_USER"],date.today(),status)
	mysql_query(sql)

def add_alert(ad_this,status,host):
	'''
	Exclude this from logs
	'''
	sql="INSERT INTO alert(alert,user,adddate,status,hosts) VALUES('{0}','{1}','{2}','{3}','{4}')".format(ad_this.strip(),os.environ["REMOTE_USER"],date.today(),status.strip(),host.strip())
	mysql_query(sql)

def get_alert():
	'''
	Returns an list with excluded objects
	'''
	sql="SELECT alert,user,adddate,id,status,hosts FROM alert ORDER BY id DESC;"
	return mysql_query(sql)


def del_alert(id):
	'''
	Deleting excludning record
	'''
	sql="delete from alert where id ='{0}'".format(id)
	mysql_query(sql)

def mysql_query(sql):
	'''
	run an mysql mysql_query
	'''
	try:
		con = None
		con = MySQLdb.Connection(mysqlhost, mysqluser, 
								mysqlpass, mysqldb)
  		curs = con.cursor()
  		curs.execute(sql)
  		con.commit()
  		
  		return curs
		
	except MySQLdb.Error, e:
		print "Error in MYSQL {0} : {1}".format(e.args[0], e.args[1])
		sys.exit(1)
	finally:
		if con:
			con.close()





