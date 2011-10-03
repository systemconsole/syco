#!/usr/bin/env python
"""
Storing passwords in a conf file with AES, protected by a master password.

This module communicates with stdin/stdout and are build to work with command
line applications.

Requires:
yum install python-crypto

Examples:
  pws=PasswordStore("/tmp/test.conf")

  # Don't ask the user for the password
  encoded = pws.set_password('mysql', 'root', 'This is my password')
  print 'Encrypted string:', encoded

  decoded = pws.get_password('mysql', 'root')
  print 'Decrypted string:', decoded

  # Will ask the user for the password the first time.
  decoded = pws.get_password('mysql', 'syscon')
  print 'Decrypted string:', decoded

Credits:
  Based on Kang Zhangs "Python Keyring Lib" project.
  http://pypi.python.org/pypi/keyring

"""

__author__ = "daniel.lindh@cybercow.se"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["Kang Zhang"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import ConfigParser
import base64
import crypt
import getpass
import os
import string
import sys
import subprocess
import time

from Crypto.Cipher import AES

class PasswordStore:

  # The block size for the cipher object; must be 16, 24, or 32 for AES.
  BLOCK_SIZE = 32

  # The character used for padding -- with a block cipher such as AES, the value
  # you encrypt must be a multiple of BLOCK_SIZE in length.  This character is
  # used to ensure that your value is always a multiple of BLOCK_SIZE.
  PADDING = '{'

  # The legal characters in an section or option name in the config file.
  LEGAL_CHARS = string.letters + string.digits

  # Where the password configfile are stored.
  file_path = None

  # The AES cipher object.
  cipher = None

  # True if the config file has been modified.
  config_file_is_modified = True

  # The config parser object.
  config = None

  # Cache of the master_password
  master_password = None

  def __init__(self, file_path):
    '''
    Set the path to the password file.

    '''
    self.file_path = file_path

    # create a cipher object using the random secret
    self.cipher = AES.new(self.get_master_password())

  def __del__(self):
    '''
    Store password file to disk.

    '''
    self.save_password_file()

  def get_master_password(self):
    '''
    Get the master password from user.

    If the master password is already stored in the password file, the user has
    to verify the password.

    If the master password are not stored in the password file, ask the user to
    write the password twice to verify that it is the right password. The
    password will then be stored in the password file.

    '''

    if (self.master_password is None):
      crypted_file_password = self._get_from_file("general", "keystore_pass")

      if (len(crypted_file_password) == 0):
        # If no password where stored in the config file, ask the user for
        # a new master password.
        master_password = self.get_password_from_user("Enter the SYCO master password: ")
      else:
        # If the password where stored in the config file, ask the user to
        # verify the master password.
        master_password = self.get_password_from_user("Verify the SYCO master password: ", False)

      master_password = self._pad(master_password)
      crypted_master_password = crypt.crypt(master_password, master_password)

      # If no file password where found, store master_password to file.
      if (len(crypted_file_password) == 0):
        self._set_to_file("general", "keystore_pass", crypted_master_password)
      else:
        if (crypted_file_password != crypted_master_password):
          raise Exception("Invalid master password")
      self.master_password = master_password

    return self.master_password

  def set_password(self, service, user_name, password):
    '''
    Encrypt and store password in password file.

    '''
    encrypted_password = base64.b64encode(self.cipher.encrypt(self._pad(password)))
    self._set_to_file(service, user_name, encrypted_password)
    return encrypted_password

  def get_password(self, service, user_name):
    '''
    Get password from the password file or from user if not defined in file.

    If the password is entered by user, it will also be stored in the password
    file. Next time the password is required, it will be retrived from the
    password file.

    '''
    crypted_file_password = self._get_from_file(service, user_name)
    user_password = self.cipher.decrypt(base64.b64decode(crypted_file_password)).rstrip(self.PADDING)

    if (len(user_password) == 0):
      user_password = self.get_password_from_user('Enter password for service "' + service + '" with username "' + user_name + '":')
      self.set_password(service, user_name, user_password)

    if (len(user_password) == 0):
      raise Exception("No password was typed for service " + service + " user " + user_name + ".")

    return user_password

  def get_password_from_user(self, password_caption="Please enter a password:", verify_password=True):
    '''
    Ask the user for a password on stdin, and validate it's strength.

    verify_password
    If True, the user has to type the password twice for veryfication.

    '''
    while (True):
      password = getpass.getpass(password_caption)

      if (verify_password):
        verify_password = getpass.getpass(password_caption + '(again) ')
        if (password != verify_password):
          sys.stderr.write("Error: Your passwords didn't match\n")
          password = verify_password
          continue
      if '' == password.strip():
        # forbid the blank password
        sys.stderr.write("Error: blank passwords aren't allowed.\n")
        password = None
        continue
      if len(password) > self.BLOCK_SIZE:
        # block size of AES is less than 32
        sys.stderr.write("Error: password can't be longer than 32.\n")
        password = None
        continue
      break
    return password

  def save_password_file(self):
    '''
    Store all passwords to file.

    '''
    if (self.config_file_is_modified):
      config_file = open(self.file_path, 'w')
      self.config.write(config_file)

      if (config_file):
        config_file.close()

  def _pad(self, s):
    '''
    Add extra padding to a password, to be valid for AES.

    '''
    padding_length = self.BLOCK_SIZE - len(s)
    if padding_length > 0:
      return s + (padding_length % self.BLOCK_SIZE) * self.PADDING
    else:
      return s

  def _build_config_parser(self):
    '''
    Build a ConfigParser with the password file data parsed.

    '''
    if (not self.config):
      self.config = ConfigParser.RawConfigParser()
      if (os.path.exists(self.file_path)):
        self.config.read(self.file_path)
    return self.config

  def _get_from_file(self, section, option):
    '''
    Get a value from the password file, in the same format it's stored in the file.

    '''
    section = self._escape_for_ini(section)
    option = self._escape_for_ini(option)
    config = self._build_config_parser()

    if (config.has_section(section) and config.has_option(section, option)):
      return config.get(section, option)
    else:
      return ""

  def _set_to_file(self, section, option, value):
    '''
    Set a value to the password file.

    The section and option name are sanitized to only allow [a-z0-8] chars.

    '''
    section = self._escape_for_ini(section)
    option = self._escape_for_ini(option)
    config = self._build_config_parser()

    if (not config.has_section(section)):
      config.add_section(section)

    config.set(section, option, value)
    self.config_file_is_modified = True

  def _escape_for_ini(self, value):
    '''
    Escapes given value so the result consists of alphanumeric chars and underscore
    only, and alphanumeric chars are preserved.

    '''
    def escape_char(c, legal=self.LEGAL_CHARS):
      '''
      Single char escape. Either normal char, or _<hexcode>

      '''
      if c in legal:
        return c
      else:
        return "_"

    return "".join(escape_char(c) for c in value)

# Test the functionality
if (__name__ == "__main__"):
  pws = PasswordStore("/tmp/test.conf")

  # Don't ask the user for the password
  encoded = pws.set_password('mysql', 'root', 'This is my password')
  print 'Encrypted string:', encoded
  decoded = pws.get_password('mysql', 'root')
  print 'Decrypted string:', decoded

  # Will ask the user for the password the first time.
  decoded = pws.get_password('mysql', 'syscon')
  print 'Decrypted string:', decoded

  print pws.get_master_password()
