#! /usr/bin/env python
#ss
#  Install the server to act as a kvm host.
#  
#  Glassfish Installation doc
#

import os, subprocess, re, ConfigParser, time
import app, general, version

# The version of this module, used to prevent
# the same script version to be executed more then
# once on the same host.
script_version = 1

def build_commands(commands):
  commands.add("install-glassfish", install_glassfish, help="Install glassfish3 on the current server.")

def install_glassfish(self):
  '''
  The actual installation of glassfish3.
  
  '''
  global script_version
  app.print_verbose("Install glassfish3 version: %d" % script_version)
  ver_obj = version.Version()
  if ver_obj.is_executed("InstallGlassfish", script_version):
    app.print_verbose("   Already installed latest version")
    return



 

  #ver_obj.mark_executed("InstallKvmHost", script_version)