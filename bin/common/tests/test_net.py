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

import net

class TestNet(unittest.TestCase):

    def test_general(self):
        self.assertEqual(net.get_all_interfaces(), {'sit0': None, 'lo': '127.0.0.1', 'eth0': '10.100.100.231'})
        self.assertEqual(net.get_interface_ip("eth0"), "10.100.100.231")
        self.assertEqual(net.get_lan_ip(), "10.100.100.231")
        self.assertEqual(net.reverse_ip("1.2.3.4"), "4.3.2.1")
        self.assertEqual(net.get_ip_class_c("1.2.3.4"), "1.2.3")
        self.assertEqual(net.num_of_eth_interfaces(), 1)
        self.assertEqual(net.get_hostname(), "fo-tp-dalitst")

if __name__ == '__main__':
    unittest.main()
