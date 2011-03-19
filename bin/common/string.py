#!/usr/bin/env python
'''
General string functions.

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

def reverse_ip(str):
	'''Reveverse in ip from 1.2.3.4 to 4.3.2.1'''
	reverse_str=""
	for num in str.split("."):
		if (reverse_str):
			reverse_str = "." + reverse_str
		reverse_str = num + reverse_str
	return reverse_str
