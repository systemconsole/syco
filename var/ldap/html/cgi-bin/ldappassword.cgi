#!/usr/bin/env python
'''
CGI for changing LDAP password.

'''

__author__ = "daniel.lindh@cybercow.se, daniel.holm@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.1"
__status__ = "Production"

import cgi
import cgitb
import subprocess

# Remove in production
# cgitb.enable()
# cgitb.enable(display=1)

# Constants set from syco
LDAP_DN = "${LDAP_DN}" # dc=syco,dc=net

class Page:
  class Message:
    '''
    Used to store error and info messages.

    '''
    message = ""

    def set_info(self, message):
      self.message = '<p class="info">' + message + "</p>"

    def set_error(self, message):
      self.message = '<p class="error">' + message + "</p>"

    def get_message(self):
      return self.message.replace("\n", "<br>")

  # Error/Info message to print on form.
  message = None

  form = None

  def __init__(self):
    self.message = Page.Message()
    self.form = cgi.FieldStorage()

  def _action(self):
    if "username" in self.form:
      user = self.form.getfirst("username", "")
      old_password = self.form.getfirst("old_password", "")
      new_password = self.form.getfirst("new_password", "")
      new_password_verification = self.form.getfirst("new_password_verification", "")

      if (len(user) == 0 or len(old_password) == 0 or len(new_password) == 0):
        self.message.set_error("Need to enter values in all fileds.")
      elif (new_password != new_password_verification):
        self.message.set_error("Password missmatch.")
      elif (new_password == old_password):
        self.message.set_error("Same password used, password is not changed.")
      else:
        self._ldappasswd(user, old_password, new_password)

  def sanitize_error(self, error):
    '''
    Convert messages returned by shellcmd ldappasswd to human readable.

    '''
    error = error.replace("Result: Constraint violation (19)", "", 1).strip()
    error = error.replace("Result: Server is unwilling to perform (53)", "", 1).strip()
    error = error.replace("Additional info:", "", 1).strip()
    error = error.replace("ldap_bind: Invalid credentials (49)", "Invalid username and/or password.")


    return error

  def _ldappasswd(self, user, old_password, new_password):
    '''
    Execute shellcmd ldappasswd to change user password.

    '''
    dn = "uid=" + user + ",ou=people," + LDAP_DN

    command = "ldappasswd -D '%(dn)s' -w '%(opsw)s' -a '%(opsw)s' -s '%(npsw)s' " % {
      'dn' : dn,
      'opsw' : old_password,
      'npsw' : new_password
    }

    envvar = {
      "LDAPTLS_CERT" : "/etc/openldap/cacerts/client.pem",
      "LDAPTLS_KEY" : "/etc/openldap/cacerts/client.pem"
    }
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=envvar)
    stdout, stderr = p.communicate()

    if p.returncode == 0:
      self.message.set_info("Password changed")
      return

    stdout += str(stderr)
    stdout = self.sanitize_error(stdout)

    self.message.set_error(stdout)

  def _get_form_html(self):
    return """
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Change LDAP Password</title>

    <style>

    /* General */

    * {
      margin: 0;
      padding: 0;
      border: 0;
    }

    body {
      font-size: 75%%;
      font-family: "Myriad Pro", Lucida, Arial sans-serif;
      text-align: center;
      background: #333;
      cursor: default;
    }

    h1 {
      padding: 0 0 0.6em;
      font-size: 1.6em;
    }

    h2 {
      padding: 1em 0 0.6em;
      font-size: 1.4em;
    }

    p {
      padding: 0.6em 0;
    }

    a {
      color: #BB6B2C;
    }

    h1 a, h2 a {
      color: #333;
    }

    a:hover {
      color: #776559;
    }

    ul {
      list-style: none;
    }

    li {
      margin-left: 10px;
    }

    label {
      display: block;
    }

    input {
      display: block;
      margin: 0.2em 0 0.5em;
      padding: 2px 3px;
      border: 1px solid #CCC;
    }

    input[type="submit"] {
      color: #fff;
      background: #444;
      border-color: #222;
    }

    pre {
      margin: 1em 0;
      padding: 0.6em 1em;
      overflow: auto;
      color: #333;
      font-family: "Courier New", monospace;
      background: #e6e6e6;
      border: 1px solid #ddd;
    }

    code {
      color: #BB6B2C;
      font-family: "Courier New", monospace;
    }

    /* Classes */

    .filename {
      font-weight: bold;
      letter-spacing: 0.2em;
    }

    .error {
      margin: 0.5em 0;
      padding: 2px 4px;
      color: #b41515;
      border: 1px solid #b41515;
      background: #efcdcd;
    }

    .info {
      margin: 0.5em 0;
      padding: 2px 4px;
      color: #1546b4;
      border: 1px solid #1546b4;
      background: #cdd2ef;
    }

    /* Specific */

    #container {
      width: 300px;
      margin: 40px auto;
      padding: 40px 50px;
      color: #333;
      font-size: 1.2em;
      text-align: left;
      background-color: #EEE;
    }

    </style>
  </head>

  <body>
    <div id="container">
      <h1>Change LDAP Password</h1>
      <form name="input" action="ldappassword.cgi" method="post">
        <div>
          <label for="">Username:</label>
          <input type="text" name="username" value="%s">
          <label for="">Old password:</label>
          <input type="password" name="old_password">
          <label for="">New password:</label>
          <input type="password" name="new_password">
          <label for="">Verify new password:</label>
          <input type="password" name="new_password_verification">
          <input type="submit" value="Change Password">
        </div>
      </form>
      %s
    </div>
  </body>
</html>
  """

  def _form(self):
    print self._get_form_html() % (self.form.getfirst("username", ""), self.message.get_message())

  def main(self):
    print "Content-Type: text/html"
    print
    self._action()
    self._form()

Page().main()
