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


def active_volgroup_name():
	"""
	Return the name of the first LVM volumegroup.

	"""
	result = x("vgdisplay --activevolumegroups -c")
	for row in result.split("\n"):
		volgroup = row.split(":", 1)[0].strip()
		if "VolGroup00" in volgroup:
			return "VolGroup00"

	raise Exception("Can't find any volgroup name.")


def create_lvm_volumegroup(name, size):
	volgroup = active_volgroup_name()
	devicename = "/dev/%s/%s" % (volgroup, name)
	result = x("lvdisplay -v " + devicename)
	if (devicename not in result):
		x("lvcreate -n %s -L %sG %s" % (name, size, volgroup))

	return devicename
