#!/usr/bin/env python
'''
NRPE check for rsyslogd status.

'''

__author__ = "anders@televerket.net"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


# UNKNOWN  - Problems with the script
# CRITICAL - The check is out of allowed boundaries.
# WARNING  - The check is close to allowed boundaries.
# OK       - The check is within allowed boundaries.
exit_codes = {'UNKNOWN':3, 'CRITICAL':2, 'WARNING':1, 'OK':0}


# NRPE checks need an exit code when the script fails.
try:
	import sys
	from optparse import OptionParser
	import MySQLdb
	import MySQLdb.cursors
except Exception, e:
	print "UNKNOWN: Failed to import mysql module: %s" % e
	sys.exit(exit_codes['UNKNOWN'])


try:
	# Define command line parameters.
	parser = OptionParser()
	parser.add_option(
		"-w", dest="warning",
		help = "Warning interval treshold, number of minimum log entries ie. 100-200",
		metavar = "WARNING",
		default = "1-2000",
		action = "store"
	)

	parser.add_option(
		"-H",
		action = "store", dest="host",
		help = "Hostname to search for syslog entries"
	)

	parser.add_option(
		"-t",
		action = "store", dest="syslogtag",
		help = "SysLogTag to search for syslog entries",
		default = "%"
	)

	# Get command line parameters.
	(options, args) = parser.parse_args()
	host = options.host
	syslogtag = options.syslogtag
	warning = options.warning.split('-')
	warning_min = int(warning[0])
	warning_max = int(warning[1])
except ValueError:
	print "UNKNOWN: --warning must have numeric value."
	sys.exit(exit_codes['UNKNOWN'])
except Exception, e:
	print "UNKNOWN: Failed to parse arguments: %s" % e
	sys.exit(exit_codes['UNKNOWN'])

if (host == None):
	parser.print_help()
	sys.exit(exit_codes['UNKNOWN'])


# Connect to rsyslog database.
try:
	#user="${MYSQL_USER}", passwd="${MYSQL_PASSWORD}", db="${MYSQL_DB}",
	mysql_conn = MySQLdb.connect(
		user="root", passwd="b0mb3r&GRANATER", db="Syslog",
		cursorclass=MySQLdb.cursors.DictCursor
	)
	db_cursor = mysql_conn.cursor()
except Exception,e:
	print "CRITICAL: Failed to connect to database: %s " % e
	sys.exit(exit_codes['UNKNOWN'])


# Check database for valid boundaries.
try:
	qry = """
	SELECT
		COUNT(ID) AS log_cnt
	FROM
		SystemEvents
	WHERE
		FromHost = %s AND
		SysLogTag like %s AND
		ReceivedAt >= DATE_SUB(NOW(), INTERVAL 1 HOUR)"""

	db_cursor.execute(qry, [host, syslogtag])
	log_hits = db_cursor.fetchone()
	log_cnt = int(log_hits['log_cnt'])
except Exception,e:
	print "CRITICAL: Failed to do sql query: %s" % e
	sys.exit(exit_codes['UNKNOWN'])


# Do the boundaries check.
if log_cnt >= warning_min and log_cnt <= warning_max:
	print "OK: Found {0} entries for host {1}.|entries={0};;;{2};{3}".format(
		log_cnt, host, warning_min, warning_max
	)
	sys.exit(exit_codes['OK'])
else:
	print "WARNING: Found {0} entries for host {1}.|entries={0};;;{2};{3}".format(
		log_cnt, host, warning_min, warning_max
	)

	sys.exit(exit_codes['WARNING'])
