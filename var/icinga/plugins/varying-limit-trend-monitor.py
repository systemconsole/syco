#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Get statistics parameters from mysql and make alerts depend on time of day.

__author__ = "Kristofer Borgström"
__maintainer__ = "Kristofer Borgström"
__email__ = "kristofer@libertar.se"
__credits__ = ["Mattias Hemmingsson"]
__version__ = "1.0.0"
__status__ = "Testing"

import MySQLdb
import sys
from datetime import datetime

"""
MYSQL Settings
"""
MYSQL_HOST = "${MYSQL_HOST}"
MYSQL_USER = "${MYSQL_USER}"
MYSQL_PASSWORD = "${MYSQL_PASSWORD}"
MYSQL_DB = "${MYSQL_DB}"

# Query should return one or more integer results
MYSQL_QUERY = "${MYSQL_QUERY}"

"""
ICINGA SETTINGS
"""

#Caption for the check
CHECK_CAPTION = "${CAPTION}"
#List of captions matching the returned values
CAPTIONS = ${MYSQL_CAPTIONS}
#TODO: support captions from mysql query

# Alert levels are for total of several parameters are returned
"""
Example dicts:
WARN = {"00-01": 10, "02-07": 0, "08-23": 30}
CRIT = {"00-01": 1, "02-07": 0, "08-23": 10}
"""
WARN = ${WARN}
CRIT = ${CRIT}

def execute_query(sql):
    """
    Run the query and return the result as a mysql cursor (iterable)
    """
    try:
        con = None
        con = MySQLdb.Connection(MYSQL_HOST, MYSQL_USER,
                                 MYSQL_PASSWORD, MYSQL_DB)
        curs = con.cursor()
        curs.execute(sql)
        con.commit()
        return curs

    except MySQLdb.Error, e:
        print "Error in MYSQL {0} : {1}".format(e.args[0], e.args[1])
        if con:
            con.close()
        sys.exit(1)
    finally:
        if con:
            con.close()


def find_current_limit(limit_dict):
    #Hour 0 through 23
    curr_hour = datetime.now().hour

    #Walk through limits to find applicable one
    for interval, limit in limit_dict.iteritems():
        interval_list = interval.split('-')
        if len(interval_list) != 2:
            print "Unexpected interval: %s, expected 2-digit hours separated by dash, e.g. '00-01'" % interval

        start = int(interval_list[0])
        end = int(interval_list[1])

        if start <= curr_hour <= end:
            return limit

    #If we ever get here, no interval was defined for now, report as error:
    print "Found no interval for hour %s" % curr_hour
    sys.exit(1)


results = execute_query(MYSQL_QUERY)

# Walk through results and build graph data and total counter
total_result = 0
additional_data = ""
caption_iter = iter(CAPTIONS)

for result_tuple in results:
    result = int(result_tuple[0])
    total_result += result
    additional_data += " '" + next(caption_iter) + "'=" + str(result)

# Check for critical level
if total_result < find_current_limit(CRIT):
    print "%s CRITICAL: |%s" % (CHECK_CAPTION, additional_data)
    sys.exit(2)

# Check for warning level
if total_result < find_current_limit(WARN):
if total_result < find_current_limit(WARN):
    print "%s WARNING: |%s" % (CHECK_CAPTION, additional_data)
    sys.exit(1)

#else OK
print "%s OK: |%s" % (CHECK_CAPTION, additional_data)
sys.exit(0)
