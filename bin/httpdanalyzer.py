#!/usr/bin/env python
'''
Analyze apache logs for the number of hits from uniques ips.

Example:

tail -f *access_log | httpdanalyzer.py

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import curses
import operator
import os
import re
import sys

# Counters
unique_ip = {}
last_request = {}
total_bytes = {}

# Curses screen
stdscr = None

# Finding columns in apache log
logpats  = r'(\S+) (\S+) (\S+) \[(.*?)\] ' \
  r'"(\S+) (\S+) (\S+)" (\S+) (\S+)'
logpat   = re.compile(logpats)

def apache_log(lines):
  '''
  Return dictionary with apache log columns.

  '''
  colnames = ('host', 'referrer', 'user', 'datetime',
    'method', 'request', 'proto', 'status', 'bytes')

  columns = logpat.match(lines)
  if (columns):
    log = dict(zip(colnames, columns.groups()))
  else:
    log = None

  return log

def update_screen():
  '''
  Print information to screen using curses.

  '''
  height, width = stdscr.getmaxyx()
  sorted_unique_ip = sorted(unique_ip.iteritems(), key=operator.itemgetter(1), reverse=True)

  txt = "Count".ljust(6, " ") + "IP".ljust(20, " ") + "Bytes".ljust(10, " ") + "Last request".ljust(200, " ")
  stdscr.addstr(0, 0, txt)
  i = 1
  for ip, count in sorted_unique_ip:
    txt = str(count).ljust(6, " ") + str(ip).ljust(20, " ") + str(total_bytes[ip]).ljust(10, " ") + last_request[ip].ljust(200, " ")
    if (txt):
      try:
        stdscr.addstr(i, 0, txt)
      except curses.error, e:
        pass
      i += 1
      if (i >= height):
        return

def collect_unique_ip():
  '''
  Collect unique ips and info from stdin.

  '''
  line = sys.stdin.readline()
  log = apache_log(line)
  if (log):
    if (log['host'] in unique_ip):
      unique_ip[log['host']] += 1
    else:
      unique_ip[log['host']] = 1
      last_request[log['host']] = ""
      total_bytes[log['host']] = 0

    last_request[log['host']] = log['request']
    try:
      total_bytes[log['host']] += int(log['bytes'])
    except ValueError, e:
      pass

def main(win):
  global stdscr
  stdscr = win
  curses.nl()
  curses.noecho()

  stdscr.timeout(0)
  stdscr.nodelay(1)

  while True:
    collect_unique_ip()
    update_screen()

    stdscr.refresh()
    stdscr.getch()

try:
  curses.wrapper(main)
except KeyboardInterrupt, e:
  pass