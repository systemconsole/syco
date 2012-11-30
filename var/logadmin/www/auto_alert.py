#!/usr/bin/env python

'''
 Auto scrit that can be trigged from nagios nrpe or over http.
 print OK if not the serach match are found i database.

 If search match is found in syslog databas and Error flag is raised

 '''

#from log_mysql import search_logs
import datetime
import subprocess
from log_mysql import mysql_query


#Setting time now and 6 hour back
now = datetime.datetime.now()
past = now - datetime.timedelta(hours=6)

def is_in_syslog_WARNING():
	'''
	Search if match is in database
	'''
	sql ="""
	select  id, Message, a.status from view_SystemEvents_compact v 
		LEFT JOIN alert a ON (v.Message LIKE concat('%',a.alert,'%')) 
			WHERE a.alert IS NOT NULL AND   
				v.DeviceReportedTime BETWEEN '{1}' AND '{0}'""".format(now.strftime("%Y-%m-%d %H:%M:%S"),past.strftime("%Y-%m-%d %H:%M:%S"))
	fromdb = mysql_query(sql)
	rows = fromdb.fetchall()
	if not rows:
		print "OK"
	else:
		for row in rows:
			print row[2]+": Match Found "+row[1]


def is_in_syslog_CRTICAL():
	'''
	Search if match is in database
	'''
	sql ="""
	select id,Message from view_SystemEvents_compact v 
		LEFT JOIN alert a ON (v.Message LIKE concat('%',a.alert,'%')) 
			WHERE a.alert IS NOT NULL AND   
				v.DeviceReportedTime BETWEEN '{1}' AND '{0}' AND a.status ='CRITICAL'""".format(now.strftime("%Y-%m-%d %H:%M:%S"),past.strftime("%Y-%m-%d %H:%M:%S"))
	fromdb = mysql_query(sql)
	rows = fromdb.fetchall()
	if not rows:
		print "OK"
	else:
		for row in rows:
			print "Match Found "+row[1]


def is_not_syslog():
	'''
	Search if dont any match if string and hos i syslog
	'''
	sql ="""
	SELECT DISTINCT a.hosts, m.FromHost, a.alert, m.Message FROM alert a 
		LEFT JOIN view_SystemEvents_compact m 
			ON 
			(m.Message LIKE CONCAT('%',a.alert,'%') 
				AND 
					a.hosts = m.FromHost 
						AND 
					m.DeviceReportedTime BETWEEN '{1}' AND '{0}')  
			WHERE m.Message IS NULL 
				AND a.status='OK'""".format(now.strftime("%Y-%m-%d %H:%M:%S"),past.strftime("%Y-%m-%d %H:%M:%S"))
	fromdb = mysql_query(sql)
	rows = fromdb.fetchall()
	if not rows:
		print "OK"
	else:
		print "CRITICAL"
		for row in rows:
			print "NOT in Syslog Host "+str(row[0])+" String: "+str(row[2])




#is_in_syslog_WARNING()
#is_in_syslog_CRTICAL()
#is_not_syslog()

now = datetime.datetime.now()
past = now - datetime.timedelta(hours=6)
now.strftime("%Y-%m-%d %H:%M:%S"),past.strftime("%Y-%m-%d %H:%M:%S")