#!/usr/bin/env python
'''
Test cases for general.py

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Test"

import unittest
import os

import app
from general import x, shell_exec

class TestGeneral(unittest.TestCase):
    def test_shell_exec(self):
        print "Will print error and stuff."
        app.options.verbose = 1

        self.assertEqual(x("uname"), "Linux\n")
        self.assertEqual(x("uname", user="root"), "Linux\n")

        app.options.verbose = 2
        self.assertEqual(x("uname"), "Linux\n")
        self.assertEqual(x("dont-exist", ), "")

        app.options.verbose = 1

if __name__ == '__main__':
    unittest.main()
