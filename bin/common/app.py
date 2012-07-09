#!/usr/bin/env python
'''
Application global wide helper functions.

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
import re
import socket
import sys
import time
import subprocess

from constant import *

# Need to be after all constants.
import options
options = options.Options()

import config
config.load(SYCO_ETC_PATH, SYCO_USR_PATH)

import install

# Syco uses packages from the EPEL repo.
# install.epel_repo()

# Required yum package.
install.package("gnupg2")
install.package("python-crypto")

# Include all password functions in app namespace.
from password import *

def print_error(message, verbose_level=1):
  '''
  Print bold error text to stdout, affected by the verbolse level.

  All error print to screen done by syco should be done with this.

  '''
  print_verbose(message, verbose_level=verbose_level, caption=BOLD + "Error: " + RESET)

def print_verbose(message, verbose_level=1, caption=None, new_line=True, enable_caption=True):
  '''
  Print a text to the stdout, affected by the verbose level.

  All print to screen done by syco should be done with this.

  #TODO: The caption are not always written ok when using new_line=False, see example at the bottom.
  #TODO: Need a output format that can be read.
  '''
  if (caption):
    caption += " "
  else:
    caption=""

  #caption = time.strftime('%Y-%m-%d %H:%M:%S') + " - " + socket.gethostname() + " - " + caption
  caption = " " + caption

  messages = []
  if (not isinstance(message, tuple)):
    messages.append(message)
  else:
    messages = message

  # Output will look like
  # syco-system: Caption This is a message
  for msg in messages:
    if (len(str(msg)) > 0):
      msg = re.sub("[\n]", "\n" + caption, str(msg))

    if (options.verbose >= verbose_level):
      msg = str(msg)
      if (enable_caption):
        msg = caption + msg

      if (new_line):
        msg += "\n"

      sys.stdout.write(msg)
      sys.stdout.flush()


if (__name__ == "__main__"):
  print_error("This is a error.")
  print_verbose("This is some text")
  long_text = '''First line
New line

Another new line

last new line'''
  print_verbose(long_text, caption="syco-vh01", new_line=False)
  print_verbose(", and some more text on the last line", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=False, enable_caption=False)
  print_verbose(".", caption="syco-vh01", new_line=True, enable_caption=False)

