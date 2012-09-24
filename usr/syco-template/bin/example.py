#!/usr/bin/env python
'''
Example of module.

'''

__author__ = "daniel.lindh@fareoffice.com"
__copyright__ = "Copyright 2011, Fareoffice Car Rental Solutions AB"
__maintainer__ = "Daniel Lindh"
__email__ = "daniel@fareoffice.com"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

def build_commands(commands):
  commands.add("example", example, "example_arg", help="This is an example.")

def example(args):
  pass

