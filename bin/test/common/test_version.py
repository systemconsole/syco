#!/usr/bin/env python
"""
Test cases for version.py

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2014, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Test"


import pytest
import os


# Need to be included before version, to prevent circular import
import app

import version


def test_version__script_init():
    version_obj = version.Version("unittest-version", 1)
    version_obj.mark_uninstalled()
    version_obj.check_executed()
    version_obj.mark_executed()

    with pytest.raises(version.VersionException):
        version_obj.check_executed()

    version_obj.mark_uninstalled()
    version_obj.check_executed()


def test_version__script_upgrade():
    version_obj = version.Version("unittest-version", 1)
    version_obj.mark_executed()

    version_obj = version.Version("unittest-version", 2)
    version_obj.check_executed()
    version_obj.mark_executed()

    with pytest.raises(version.VersionException):
        version_obj.check_executed()

    version_obj.mark_uninstalled()
    version_obj.check_executed()


def test_version__app_init():
    version_obj = version.Version("unittest-version", 1, '1.12.34b')
    version_obj.mark_uninstalled()
    version_obj.check_executed()
    version_obj.mark_executed()

    with pytest.raises(version.VersionException):
        version_obj.check_executed()

    version_obj.mark_uninstalled()
    version_obj.check_executed()


def test_version__app_upgrade():
    version_obj = version.Version("unittest-version", 1, '1.12.34b')
    version_obj.mark_executed()

    version_obj = version.Version("unittest-version", 1, '1.12.35b')
    version_obj.check_executed()
    version_obj.mark_executed()

    with pytest.raises(version.VersionException):
        version_obj.check_executed()

    version_obj.mark_uninstalled()
    version_obj.check_executed()


def test_version__reset_file():
    version_obj = version.Version("unittest-version", 1, '1.12.34b')
    version_obj.mark_executed()
    version_obj.reset_version_file()
    assert os.path.exists(version_obj.config_file_name) == False
    version_obj.mark_executed()
    assert os.path.exists(version_obj.config_file_name) == True
