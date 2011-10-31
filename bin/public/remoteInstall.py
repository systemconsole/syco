#!/usr/bin/env python
'''
Execute commands on the remote hosts defined in etc/install.cfg

'''

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import os
import socket
import sys
import threading
import time

import app
import config
import general
import pexpect
import pxssh
import ssh
from exception import SettingsError

def build_commands(commands):
  commands.add("remote-install",      remote_install,      "[hostname]", help="Connect to all servers, and run all commands defined in install.cfg.")
  commands.add("install-local",       install_local,       "[hostname]", help="Run all commands defined in install.cfg.")
  commands.add("remote-install-syco", remote_install_syco, "[hostname]", help="Install syco on a remote host.")

def remote_install(args):
  '''
  '''
  # Ask the user for all passwords that might be used in the remote install
  # so the installation can go on headless.
  app.init_all_passwords()

  # Start installation timer.
  t0= time.time()

  remote_host = None
  if len(args) > 1:
    remote_host = args[1]

  obj = RemoteInstall()
  obj.run(remote_host)

  # Print the time it took to install all servers.
  t= time.time() - t0 # t is CPU seconds elapsed (floating point)
  print "It took " + time.strftime('%X', time.gmtime(t)) + " to install all servers."

def install_local(args):
  '''
  Run all commands on the localhost.

  '''
  # Ask the user for all passwords that might be used in the remote install
  # so the installation can go on headless.
  app.init_all_passwords()

  hostname = ""
  if len(args) > 1:
    hostname = args[1]

  if hostname == "":
    hostname = socket.gethostname()
  app.print_verbose("Install all commands defined in install.cfg for host " + hostname + ".")

  commands = config.host(hostname).get_commands(app.options.verbose >= 2)
  if len(commands) > 0:
    for command in commands:
      general.shell_exec(command)
  else:
    app.print_error("No commands for this host.")

def remote_install_syco(args):
  '''
  '''
  # Ask the user for all passwords that might be used in the remote install
  # so the installation can go on headless.
  app.init_all_passwords()

  remote_host = None
  if len(args) > 1:
    remote_host = args[1]

  obj = RemoteInstall()
  obj.remote_install_syco(remote_host)


class RemoteInstall:
  '''
  Run commands defined in install.cfg on remote hosts through SSH.

  If the remote host is not yet installed/started/available,
  the script will retry to connect every 30 second until it answers.

  '''
  servers = []

  # All hosts that are alive.
  alive = {}

  # All hosts config status
  invalid_config = {}

  # All hosts that has been installed.
  installed = {}

  # Abort error
  abort_error = {}

  def run(self, hostname=""):
    '''
    Start the installation

    '''
    self._set_servers(hostname)
    self._validate_install_config()
    self._start_all_threads()
    self._wait_for_all_threads_to_finish()

  def remote_install_syco(self, hostname):
    '''
    Execute the commands on the remote host.

    Create one process for each remote host.

    '''
    try:
      server = config.host(hostname).get_back_ip()
      app.print_verbose("Install syco on " + hostname + " (" + server + ")", 2)

      obj = ssh.Ssh(server, app.get_root_password())
      self._validate_alive(obj, hostname)
      obj.install_ssh_key()
      self._install_syco_on_remote_host(obj)

    except pexpect.EOF, e:
      app.print_error(e, 2)

    except SettingsError, e:
      app.print_error(e, 2)

  def _start_all_threads(self):
    while(not self._is_all_servers_installed()):
      self._print_install_stat()

      for hostname in self.servers:
        if (not self._is_installation_in_progress(hostname) and not self.has_abort_errors(hostname)):
          self.installed[hostname] = "Progress"
          t = threading.Thread(target=self._install_host, args=[hostname])
          t.start()

      # End script if all threads are done, otherwise sleep for 30
      for i in range(30):
        time.sleep(1)
        if(self._is_all_servers_installed()):
          return

    # Wait for all threads to finish
  def _wait_for_all_threads_to_finish(self):
    for t in threading.enumerate():
      if (threading.currentThread() != t):
        t.join()

  def _is_all_servers_installed(self):
    return len(self.servers) == self._installed_servers()

  def _installed_servers(self):
    installed = 0
    for status in self.installed.values():
      if (status == "Yes"):
        installed += 1

    return installed

  def _servers_left_to_install(self):
    return len(self.servers) - self._installed_servers()

  def _is_installation_in_progress(self, hostname):
    if (hostname in self.installed and self.installed[hostname] != "No"):
      return True
    else:
      return False

  def has_abort_errors(self, hostname):
    return (hostname in self.abort_error)

  def _install_host(self, hostname):
    '''
    Execute the commands on the remote host.

    Create one process for each remote host.

    '''
    try:
      server = config.host(hostname).get_back_ip()
      app.print_verbose("Try to install " + hostname + " (" + server + ")", 2)

      obj = ssh.Ssh(server, app.get_root_password())
      self._validate_alive(obj, hostname)
      app.print_verbose("========================================================================================")
      app.print_verbose("=== Update " + hostname + " (" + server + ")")
      app.print_verbose("========================================================================================")

      obj.install_ssh_key()
      self._install_syco_on_remote_host(obj)
      self._execute_commands(obj, hostname)

    except pexpect.EOF, e:
      app.print_error(e, 2)

      # Remove progress state.
      if hostname in self.installed:
        del(self.installed[hostname])

    except SettingsError, e:
      app.print_error(e, 2)

      # Remove progress state.
      if hostname in self.installed:
        del(self.installed[hostname])

  def _install_syco_on_remote_host(self, ssh):
    '''
    Rsync syco to remote server, and install it

    '''
    app.print_verbose("Install syco on remote host")
    ssh.rsync(app.SYCO_PATH, app.SYCO_PATH, "--exclude version.cfg")
    ssh.ssh_exec(app.SYCO_PATH + "bin/syco.py install-syco")

  def _execute_commands(self, obj, hostname):
    commands = config.host(hostname).get_commands(app.options.verbose >= 2)

    while(len(commands) != 0):
      try:
        obj.ssh_exec(commands[0])
        commands.pop(0)
      except ssh.SSHTerminatedException, e:
        app.print_error("SSHTerminatedException on host " + hostname + " with command " + commands[0])
        obj.wait_until_alive()

      except pexpect.EOF, e:
        app.print_error("pexpect.EOF on host " + hostname + " with command " + commands[0])

      except pxssh.ExceptionPxssh, e:
        app.print_error("pxssh.ExceptionPxssh on host " + hostname + " with command " + commands[0] + ", might be because the remote host rebooted.")

    self.installed[hostname] = "Yes"
    app.print_verbose("")

  def _set_servers(self, hostname):
    '''
    Set servers/hosts to perform the remote install on.

    '''
    if (hostname):
      self.servers.append(hostname)
      if (config.host(hostname).is_host()):
        self.servers += config.host(hostname).get_guests()
    else:
      self.servers = config.get_servers()

    sorted(self.servers)

  def _validate_install_config(self):
    '''
    Validate all host options in install.cfg.

    Print error messages in verbose mode.

    '''
    for hostname in self.servers:
      if (not config.host(hostname).get_back_ip()):
        self.invalid_config[hostname] = "No"
        app.print_verbose("In install.cfg, cant find ip for " + hostname)
      else:
        self.invalid_config[hostname] = "Yes"

  def _validate_alive(self, ssh_obj, hostname):
    if (ssh_obj.is_alive()):
      self.alive[hostname] = "Yes"
    else:
      self.alive[hostname] = "No"
      raise SettingsError(hostname + " is not alive.")

  def _print_install_stat(self):
    '''
    Display information about the servers that are being installed.

    '''
    print("\n\n\n")
    app.print_verbose(str(self._servers_left_to_install()) + " server(s) left to install.")
    app.print_verbose(str(threading.activeCount()) + " thread(s) are running.")
    app.print_verbose("   " +
      "SERVER NAME".ljust(30) +
      "IP".ljust(15) +
      "ALIVE".ljust(6) +
      "VALID CONFIG".ljust(13) +
      "INSTALLED".ljust(10) +
      "ABORT ERROR".ljust(20)
      )
    app.print_verbose("   " +
      ("-" * 29).ljust(30) +
      ("-" * 14).ljust(15) +
      ("-" * 5).ljust(6) +
      ("-" * 12).ljust(13) +
      ("-" * 9).ljust(10) +
      ("-" * 20).ljust(21)
      )
    for hostname in self.servers:
      app.print_verbose("   " +
        hostname.ljust(30) +
        config.host(hostname).get_back_ip().ljust(15) +
        self._get_alive(hostname).ljust(6) +
        self._get_invalid_config(hostname).ljust(13) +
        self._get_installed(hostname).ljust(10) +
        self._get_abort_errors(hostname)
        )
    print("\n\n\n")

  def _get_alive(self, hostname):
    if (hostname in self.alive):
      return self.alive[hostname]
    else:
      return "?"

  def _get_invalid_config(self, hostname):
    if (hostname in self.invalid_config):
      return self.invalid_config[hostname]
    else:
      return "?"

  def _get_installed(self, hostname):
    if (hostname in self.installed):
      return self.installed[hostname]
    else:
      return "No"

  def _get_abort_errors(self, hostname):
    if (hostname in self.abort_error):
      return str(self.abort_error[hostname])
    else:
      return "?"
