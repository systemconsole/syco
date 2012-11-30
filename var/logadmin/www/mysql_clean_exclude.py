#!/usr/bin/env python

'''
 DELETE v from SystemEvents v LEFT JOIN Exclude e ON (v.Message LIKE concat('%',e.exclude,'%')) WHERE e.exclude IS NOT NULL AND 
 v.DeviceReportedTime BETWEEN '2012-11-15 00:00:00' AND '2012-11-15 23:59:59' AND e.status = "DELETE";

 '''

#from log_mysql import search_logs
from datetime import date, timedelta
import subprocess
from log_mysql import mysql_query

def clean_mysql():
	'''
	Cleaning out mysql from delete strings inserted into logadmin site.
	Run every day to clean out from non intressted log enteris.
	'''

	#What date to use for deleteing
	sql="""
	DELETE 
		v 
	from 
		SystemEvents v 
			LEFT JOIN Exclude e ON (v.Message LIKE concat('%',e.exclude,'%')) 
		WHERE 
			e.exclude IS NOT NULL AND  
			v.DeviceReportedTime BETWEEN '{0} 00:00:00' AND '{0} 23:59:59' AND 
		e.status = 'DELETE'""".format(date.today())
	
	#Runningg sql
	mysql_query(sql)
	
	#Logging to syslog
	logthis ="logger -t syco-task -s 'Cleaning logserver mysql from excludes'"
	subprocess.Popen(logthis.split())





clean_mysql()

	