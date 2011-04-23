#!/usr/bin/env python
'''
CGI for changing LDAP password.

'''

__author__ = "mattias@fareoffice.com"
__copyright__ = "Copyright 2011, The System Console project"
__maintainer__ = "Daniel Lindh"
__email__ = "syco@cybercow.se"
__credits__ = ["???"]
__license__ = "???"
__version__ = "1.0.0"
__status__ = "Production"

import cgi
import cgitb
import ldap

# Remove in production
# cgitb.enable()
# cgitb.enable(display=0, logdir="/tmp")

# Constants set from syco
LDAP_DN = "${LDAP_DN}"              # dc=fareonline,dc=net
LDAP_HOSTNAME = "${LDAP_HOSTNAME}"  # ldap.fareonline.net

def action():
  message = ""
  form = cgi.FieldStorage()
  
  if "username" in form:
    user = form.getfirst("username", "")
    old_password = form.getfirst("old_password", "")
    new_password = form.getfirst("new_password", "")
    new_password_verification = form.getfirst("new_password_verification", "")
    #shell_exec("ldap change password")
    if (new_password != new_password_verification):
      message = "Password missmatch."
    elif (new_password == old_password):
      message = "Same password used, password is not changed."
    else:
      message = change_password(user, old_password, new_password)

  return message

def change_password(user, old_password, new_password):
  message = ""
  l = ""
  try:
    dn = "uid=" + user + ",ou=people," + LDAP_DN
    l = ldap.initialize("ldap://" + LDAP_HOSTNAME)
    l.set_option(ldap.OPT_X_TLS_DEMAND, True)
    l.start_tls_s()
    l.simple_bind_s(dn, old_password)
    l.passwd_s(dn, old_password, new_password)
    message = "Password changed"
  except ldap.UNWILLING_TO_PERFORM, e:
    message = "Unwilling to perform operation."
  except ldap.INVALID_CREDENTIALS, e:
    message = "Invalid username and or password."
  except ldap.LDAPError, e:
    if "info" in e[0]:
      message += "Error: " + str(e[0]['info'])
      if "desc" in e[0]:
        message += " (" + str(e[0]['desc']) + ")."
    elif hasattr(e, 'message'):
      if type(e.message) == dict:
        for (k, v) in e.message.iteritems():
          message += "%s: %sn\n" % (k, v)
      else:
        message += "Error: %sn\n" % e.message
    else:
      message += "Error: " + str(e)
  try:
    l.unbind()
  except:
    pass
  
  return message

def _get_form_html():
  return """
<HTML>
<HEAD>
 <TITLE>Change LDAP password.</TITLE>
</HEAD>
<BODY>
 <H1>Change LDAP password.</H1>
 <form name="input" action="ldappassword.cgi" method="post">
   Username: <input type="text" name="username" value="%s"/>
   Old password: <input type="password" name="old_password" />
   New password: <input type="password" name="new_password" />
   Verify new password: <input type="password" name="new_password_verification" />
   <input type="submit" value="Submit" />
 </form>
 <div>%s</div>
</BODY>
</HTML>
"""

def form(message):
  
  print _get_form_html() % (cgi.FieldStorage().getfirst("username", ""), message)
  print cgi.FieldStorage().getfirst("username", "")

def main():
  print "Content-Type: text/html"
  print
  message = action()
  form(message)

main()