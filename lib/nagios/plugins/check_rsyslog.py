#!/usr/bin/env python
exit_codes = {'UNKNOWN':3,'CRITICAL':2,'WARNING':1,'OK':0}

import sys
#Some basic sanity checks
try:
	import MySQLdb
	import MySQLdb.cursors
except Exception, e:
	print "CRITICAL: Failed to import mysql module: %s" % e
	sys.exit(exit_codes['CRITICAL'])
	
try:
	mysql_conn = MySQLdb.connect(user="${MYSQL_USER}",passwd="${MYSQL_PASSWORD}",db="${MYSQL_DB}", cursorclass=MySQLdb.cursors.DictCursor)
	db_cursor = mysql_conn.cursor()
except Exception,e:
	print "CRITICAL: Failed to connect to database: %s " % e
	sys.exit(exit_codes['CRITICAL'])

qry = """SELECT COUNT(ID) AS log_cnt FROM SystemEvents WHERE FromHost = %s
	  AND ReceivedAt >= DATE_SUB(NOW(),INTERVAL 1 HOUR)"""
	
from optparse import OptionParser
parser = OptionParser()
parser.add_option("-w", "--warning", dest="warning",
				  help="Warning treshold, number of minimum log entries",
				  metavar="WARNING",
				  default="1",
				  action="store")
parser.add_option("-n", "--host",
				  action="store", dest="host",
				  help="Hostname to search for syslog entries")


(options, args) = parser.parse_args()

try:
	host = options.host
	warning = int(options.warning)
except Exception,e:
	print "UNKNOWN: Failed to parse arguments: %s" % e
	sys.exit(exit_codes['UNKNOWN'])
	
if ( host == None):
	parser.print_help()
	sys.exit(exit_codes['UNKNOWN'])
	
	
try:
	db_cursor.execute(qry,[host])
	log_hits = db_cursor.fetchone()
	log_cnt = int(log_hits['log_cnt'])
except Exception,e:
	print "CRITICAL: Failed to do sql query: %s" % e
	sys.exit(exit_codes['CRITICAL'])
	


if log_cnt >= warning:
	print "OK: Found %i entries for host %s" %(log_cnt,host)
	sys.exit(exit_codes['OK'])
else:
	print "WARNING: Found %i entries for host %s" %(log_cnt,host)
	sys.exit(exit_codes['WARNING'])

	