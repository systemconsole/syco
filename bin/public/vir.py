#!/usr/bin/env python
'''
Helper functions to control a KVM host.

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
import config
import general
import ssh
from exception import SettingsError

def build_commands(commands):
  commands.add("vir-rm", vir_rm, "[server]", help="Remove a KVM guest from this KVM host.")
  commands.add("vir-list", vir_list, help="List all KVM guests on all KVM hosts.")

def vir_rm(args):
  # TODO: Check if this is a KVM host
  server_name = args[1]
  app.print_verbose("Remove virtual server %s." % server_name)

  app.print_verbose("Destory the kvm instance");
  general.shell_exec("virsh destroy " + server_name)
  general.shell_exec("virsh undefine " + server_name)

  general.remove_file("/var/log/libvirt/qemu/" + server_name + ".log")

  general.shell_exec("lvremove -f /dev/VolGroup00/" + server_name)

  app.print_verbose("Restart libvirtd");
  general.shell_exec("/etc/init.d/libvirtd restart")
  general.shell_exec("updatedb")

def vir_list(args):
  old_verbose = app.options.verbose
  app.options.verbose = 2
  try:
    for hostname in config.get_hosts():
      server = config.host(hostname).get_front_ip()

      obj = ssh.Ssh(server, app.get_root_password())

      app.print_verbose("List KVM guests on host " + hostname + " (" + server + ")")
      if (obj.is_alive()):
        obj.install_ssh_key()
        obj.ssh_exec("virsh list --all")
      else:
        app.print_verbose("   Not online.")
  except SettingsError, e:
    app.print_error(e, 2)

  app.options.verbose = old_verbose
