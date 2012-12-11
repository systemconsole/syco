#!/usr/bin/env python
'''
Test cases for config.py

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

#from common.passwordstore import PasswordStore

class TestPasswordStore(unittest.TestCase):
    pass

#     def test_passwordstore(self):
#         pws = PasswordStore("/tmp/test.conf")

#         # Don't ask the user for the password
#         encoded = pws.set_password('mysql', 'root', 'This is my password')
#         self.assertEqual(encoded, 'ftph29Rn1VrdY1vufNz3+sfNMpHKfU0dUrBucm01Th4=')

#         decoded = pws.get_password('mysql', 'root')
#         self.assertEqual(decoded, 'This is my password')

if __name__ == '__main__':
    unittest.main()
