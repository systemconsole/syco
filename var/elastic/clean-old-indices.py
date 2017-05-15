#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = "Kristofer Borgström"
__credits__ = "Mattias Hemmingsson"

import sys, getopt, urllib2, datetime, base64, os


def usage():
    print("clean-old-indices.py [-h <elastic host>] [-u <basic-auth-username>] [-p <basic-auth-password>] <index> <days-to-keep>")
    print("Example: python clean-old-indices.py -h 1.1.1.1 logstash-syslog 90")
    print("Default host is: localhost")


def es_execute(hostname, path, method="GET", user=None, passwd=None):
    """
    Run the command against the elasticsearch server
    """

    url = "http://{0}:9200/{1}".format(hostname, path)

    req = urllib2.Request(url)

    # Do basic auth
    if (user and passwd):
        print("Using basic auth, user: %s" % user)
        base64string = base64.b64encode('%s:%s' % (user, passwd))
        req.add_header("Authorization", "Basic %s" % base64string)

    req.get_method = lambda: method

    res = urllib2.urlopen(req)
    return res.read()


try:
    # Parse the arguments and options
    argv = sys.argv[1:]
    opts, args = getopt.getopt(argv, "h: u: p:")

    if len(args) < 2:
        raise getopt.GetoptError("Insufficient arguments")

    host = "localhost"
    user = None
    passwd = None
    for o, a in opts:
        if o == '-h':
            host = a
        elif o == '-u':
            user = a
        elif o == '-p':
            passwd = a

    arg_iter = iter(args)
    index_name = arg_iter.next()
    days = int(arg_iter.next())

    # Index cutoff definition, remove older than this date
    earliest_to_keep = datetime.date.today() - datetime.timedelta(days=days)

    index_cutoff = "{0}-{1}".format(index_name, earliest_to_keep.strftime("%Y.%m.%d"))

    all_indices = es_execute(host, '_cat/indices', user=user, passwd=passwd)

    for line in all_indices.splitlines():
        index = line.split(" ")[2]
        if index.startswith(index_name) and index < index_cutoff:
            print("Deleting index: %s" % index)
            os.system('logger -t elastic-index-cleanup "[INFO] Deleting index: %s"' % index)
            es_execute(host, index, method="DELETE", user=user, passwd=passwd)

except getopt.GetoptError as err:

    os.system('logger -t elastic-index-cleanup "[ERROR] GetoptError: %s"' % err)
    print('[ERROR] GetoptError: %s"' % err)
    usage()
    sys.exit(2)

except urllib2.HTTPError as err:
    os.system('logger -t elastic-index-cleanup "[ERROR] GetoptError: %s"' % err)
    print('[ERROR] HTTPError: %s"' % err)
    sys.exit(2)

