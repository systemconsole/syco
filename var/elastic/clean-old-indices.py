#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = "Kristofer Borgström"
__credits__ = "Mattias Hemmingsson"

import sys, getopt, urllib2, datetime


def usage():
    print "clean-old-indices.py [-h <elastic host>] <index> <days-to-keep>"
    print "Example: python -h 1.1.1.1 clean-old-indices.py logstash-syslog 90"
    print "Default host is: localhost"


def es_execute(hostname, path, method="GET"):
    """
    Run the command against the elasticsearch server
    """

    url = "http://{0}:9200/{1}".format(hostname, path)

    req = urllib2.Request(url)
    req.get_method = lambda: method

    res = urllib2.urlopen(req)

    return res.read()


try:
    # Parse the arguments and options
    argv = sys.argv[1:]
    opts, args = getopt.getopt(argv, "h:")

    if len(args) != 2:
        raise getopt.GetoptError("")

    host = "localhost"
    for o, a in opts:
        print o
        if o == '-h':
            host = a

    arg_iter = iter(args)
    index_name = arg_iter.next()
    days = int(arg_iter.next())

    # Index cutoff definition, remove older than this date
    earliest_to_keep = datetime.date.today() - datetime.timedelta(days=days)

    index_cutoff = "{0}-{1}".format(index_name, earliest_to_keep.strftime("%Y.%m.%d"))

    all_indices =  es_execute(host, '_cat/indices')

    for line in all_indices.splitlines():
        index = line.split(" ")[2]

        if index.startswith(index_name) and index < index_cutoff:
            print "Deleting index: %s"% index
            es_execute(host, index, method="DELETE")

except getopt.GetoptError:
    usage()
    sys.exit(2)

