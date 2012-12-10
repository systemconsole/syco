#!/usr/bin/python
'''
Executes all unit tests that are found in the project according to the
pattern set with "--pattern". Default pattern is test*.py. It will recursively
go through all directories looking for files matching the pattern.

This is a modified version of the test-all from the https://github.com/oan/oand
project.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, Amivono AB"
__maintainer__ = "daniel.lindh@cybercow.se"
__license__ = "We pwn it all."
__version__ = "0.1"
__status__ = "Test"

from optparse import OptionParser
import os
import os.path
import sys
import trace
import unittest

# Command line options.
OPTIONS = None

# Command line positional arguments.
ARGS = None

# KeybordInterrupt
KEYBOARD_INT = None

def run():
    setup_env()
    set_global_options_and_args()
    execute_tests()


def setup_env():
    '''Add all folders including src code to the "import-path"'''
    sys.path.insert(0, get_base_dir() + "bin/common/")


def get_base_dir():
    '''Return the path to the root folder of the project.'''
    return os.path.abspath(__file__).rsplit('/', 2)[0] + "/"


def set_global_options_and_args():
    '''Set cmd line arguments in global vars OPTIONS and ARGS.'''
    global OPTIONS, ARGS

    usage = "usage: %prog [-t] -p pattern"

    parser = OptionParser(usage=usage)

    parser.add_option("-q", "--quiet", default=1,
                      action="store_const", const=0, dest="verbose",
                      help="No output to screen.")

    parser.add_option("-p", "--pattern", default='test*.py',
                      dest="pattern",
                      help="The search pattern to use when finding tests.")

    (OPTIONS, ARGS) = parser.parse_args()


def execute_tests():
    '''Execute all testcases.'''

    unittest.TextTestRunner(stream=sys.stderr, descriptions=True, verbosity=1).run(suite())


def suite():
    '''Setup a test suit with all testcases'''
    test_root_folder = get_base_dir() + 'test/'
    print("Add tests from %s" % test_root_folder)
    return unittest.defaultTestLoader.discover(test_root_folder, OPTIONS.pattern)


if __name__ == '__main__':
    run()
