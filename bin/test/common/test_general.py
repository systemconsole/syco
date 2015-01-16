#!/usr/bin/env python
"""
Test cases for general.py

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2014, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Test"


import os
import pytest


# Need to be included before version, to prevent circular import
import app

import general


def test_general__require_linux_user():
    with pytest.raises(version.Exception):
        general.require_linux_user('xxx')


def test_general__require_linux_user():
    with pytest.raises(version.Exception):
        general.require_linux_user('xxx')
