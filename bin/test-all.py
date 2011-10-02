#!/usr/bin/env python
'''
This script runs all tests in a directory. It does not need to know about the
tests ahead of time. It recursively descends from the current directory and
automatically builds up a list of tests to run. Only directories named 'tests'
are processed. The path to each 'tests' directory is added to the PYTHONPATH.
Only python scripts that start with 'test_' are added to the list of scripts in
the test suite.

This script is heavly based on Noah Spurriers testall.py script that are used
with pexpect. Original URL
http://pexpect.svn.sourceforge.net/viewvc/pexpect/trunk/pexpect/tools/testall.py?revision=447&view=markup

'''

__author__ = "Noah Spurrier"
__maintainer__ = "daniel.lindh@cybercow.se"

import unittest
import os, os.path
import sys
import trace

def get_project_home():
    '''Return the path to the root folder of the project.'''
    project_home = os.path.realpath(__file__)
    project_home = os.path.split(project_home)[0]
    project_home = os.path.split(project_home)[0]
    return project_home

def add_tests_to_list (import_list, dirname, names):
  # Only check directories named 'tests'.
  if os.path.basename(dirname) != 'tests':
    return
  # Add any files that start with 'test_' and end with '.py'.
  for f in names:
    filename, ext = os.path.splitext(f)
    if ext != '.py':
      continue
    if filename.find('test_') == 0:
      import_list.append (os.path.join(dirname, filename))

def find_modules_and_add_paths (root_path):
  import_list = []
  module_list = []
  os.path.walk (root_path, add_tests_to_list, import_list)
  for module_file in import_list:
    path, module = os.path.split(module_file)
    module_list.append (module)
    print 'Adding:', module_file
    if not path in sys.path:
      sys.path.append (path)
    if not os.path.dirname(path) in sys.path:
      sys.path.append (os.path.dirname(path))
  module_list.sort()
  return module_list

def suite():
  modules_to_test = find_modules_and_add_paths(os.getcwd())
  alltests = unittest.TestSuite()
  for module in map(__import__, modules_to_test):
    alltests.addTest(unittest.findTestCases(module))

  return alltests

def main():
    unittest.main(defaultTest='suite')

def remove_cmd_line_arguments():
    del sys.argv[1:]

def setup_env():
    sys.path.insert(1, get_project_home())
    os.chdir(get_project_home())

def run_main_with_trace():
    # create a Trace object, telling it what to ignore, and whether to
    # do tracing or line-counting or both.
    tracer = trace.Trace(
        ignoredirs=[sys.prefix, sys.exec_prefix],
        trace=0,
        count=1,
        countfuncs=1,
        countcallers=1,
        infile='/tmp/cover.tmp',
        outfile='/tmp/cover.tmp')

    # run the new command using the given tracer
    tracer.run('main()')

    # make a report, placing output in /tmp
    r = tracer.results()
    r.write_results(show_missing=True, summary=True, coverdir="/tmp")

if __name__ == '__main__':
    setup_env()
    remove_cmd_line_arguments()
    run_main_with_trace()
