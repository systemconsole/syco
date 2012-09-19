#!/usr/bin/env python
'''
Functions to handle NFS exports.

Read more.
http://www.crazysquirrel.com/computing/debian/servers/setting-up-nfs4.jspx
http://aaronwalrath.wordpress.com/2011/03/18/configure-nfs-server-v3-and-v4-on-scientific-linux-6-and-red-hat-enterprise-linux-rhel-6/

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import app
from general import x, set_config_property
import iptables

def add_export(name, path, clients="*", permissions="rw,sync,nohide"):
  '''
  Add a folder for nfs export.

  Example
  add_export("dvd", "/media/dvd")
  Will create the export /exports/dvd

  '''
  x("mkdir -p /exports/" + name)
  x("chmod 755 /exports/")
  x("mount --bind " + path + " /exports/" + name)
  x("chmod 755 " + path + " /exports/" + name)

  set_config_property(
    "/etc/fstab",
    "^%s.*$" % (path),
    "%s /exports/%s none bind 0 0" % (path, name)
  )

  # Add for example /exports/log *(rw,sync,nohide)
  set_config_property(
    "/etc/exports",
    "^/exports/%s.*$" % (name),
    "/exports/%s %s(%s)" % (name, clients, permissions)
  )

  # Only needed once, but is dublicate here.
  set_config_property("/etc/exports", "\/exports \*\(ro\,fsid\=0\)", "/exports *(ro,fsid=0)")

  # TODO : Using thease mount parameters?
  #set_config_property("/etc/exports", "^" + name + ".*$", name + " *(rw,sync,nohide,insecure,root_squash,no_subtree_check,fsid=0)")

def remove_export(name):
  x("umount /exports/" + name)
  set_config_property("/etc/exports", "^/exports/" + name + ".*$", "")

  set_config_property("/etc/fstab", "^.*/exports/%s.*$" % (name), "")


def restart_services():
  x("exportfs -rv")
  x("setsebool -P nfs_export_all_rw 1")
  x("service rpcbind restart")
  x("service nfs restart")
  x("service nfslock restart")
  x("service rpcsvcgssd restart")

def stop_services():
  x("service rpcsvcgssd stop")
  x("service nfslock stop")
  x("service nfs stop")
  x("service rpcbind stop")

def enable_services_autostart():
  x("chkconfig rpcsvcgssd on")
  x("chkconfig nfslock on")
  x("chkconfig nfs on")
  x("chkconfig rpcbind on")

def disable_services_autostart():
  x("chkconfig --level 12345 rpcsvcgssd off")
  x("chkconfig --level 12345 nfslock off")
  x("chkconfig --level 12345 nfs off")
  x("chkconfig --level 12345 rpcbind off")

def configure_with_static_ip():
  '''
  http://www.cyberciti.biz/faq/centos-fedora-rhel-iptables-open-nfs-server-ports/

  @TODO: Should be named configure_with_static_ports.

  '''
  app.print_verbose("Configure nfs static server ports.")
  # TCP port rpc.lockd should listen on.
  set_config_property("/etc/sysconfig/nfs", ".*LOCKD_TCPPORT.*", "LOCKD_TCPPORT=32803")

  # UDP port rpc.lockd should listen on.
  set_config_property("/etc/sysconfig/nfs", ".*LOCKD_UDPPORT.*", "LOCKD_UDPPORT=32769")

  # Port rpc.mountd should listen on.
  set_config_property("/etc/sysconfig/nfs", ".*MOUNTD_PORT.*", "MOUNTD_PORT=892")

  # Port rquotad should listen on.
  set_config_property("/etc/sysconfig/nfs", ".*RQUOTAD_PORT.*", "RQUOTAD_PORT=875")

  # Port rpc.statd should listen on.
  set_config_property("/etc/sysconfig/nfs", ".*STATD_PORT.*", "STATD_PORT=662")

  # Outgoing port statd should used. The default is port is random
  set_config_property("/etc/sysconfig/nfs", ".*STATD_OUTGOING_PORT.*", "STATD_OUTGOING_PORT=2020")

def add_iptables_rules():
  '''
  Open iptables for NFS just during the installation.

  '''
  iptables.add_nfs_chain()
  iptables.save()

def remove_iptables_rules():
  iptables.del_nfs_chain()
  iptables.save()
