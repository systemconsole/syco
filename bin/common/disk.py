#!/usr/bin/env python
"""
Disk functions.

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"


from general import x


def verify_volgroup(vol_group_name):
    """
    Return the name of the first LVM volumegroup.

    """
    result = x("vgdisplay --activevolumegroups -c")
    for row in result.split("\n"):
        volgroup = row.split(":", 1)[0].strip()
        if vol_group_name in volgroup:
            return

    raise Exception("Can't find VolGroup named: %s" % (vol_group_name))


def create_lvm_volumegroup(name, size, vol_group = "VolGroup00"):
    verify_volgroup(vol_group)
    device_name = "/dev/%s/%s" % (vol_group, name)
    result = x("lvdisplay -v " + device_name)
    if device_name not in result:
        x("lvcreate -n %s -L %sG %s" % (name, size, vol_group))

    return device_name
