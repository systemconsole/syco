#!/usr/bin/env python
 
import cgi
import os
from datetime import date, timedelta
from log_mysql import search_logs, logs_are_signed, sign_logs, add_exclude

import cgitb; cgitb.enable()  # for troubleshooting
# Create instance of FieldStorage 
form = cgi.FieldStorage() 

#Setting date for site
if form.getvalue('view_date'):
	view_date = form.getvalue('view_date')
else:
	view_date = date.today()






print "Content-type: text/html"

print """
<html> 
<head>
	<LINK href="css/bootstrap.css" rel="stylesheet" type="text/css">
	<title>Syco LogAdmin</title></head> 
<body> 
 """

#excludning
#Excluding records
if form.getvalue('exclude'):
	exclude = form.getvalue('exclude')
	add_exclude(exclude)

	print """
	<div class="alert alert-warning">
  	<h4>You have exclude <b>{0}</b> from the log search
  	</div>
	""".format(exclude)

#Signing yestordays logs
if form.getvalue('user'):
	time = form.getvalue('view_date')
	user  = form.getvalue('user')
	mess  = form.getvalue('mess')
	sign_logs(time,user,mess,date.today())

	print """
	<div class="alert alert-success">
  	<h4>You have signet the date <b>{0}</b> with the user <b>{1}</b> Sucessfully
  	</div>
	""".format(time,user)
 
#If logs are signed
signed = logs_are_signed(view_date)

print """
<div div class="container">
<div class="navbar">
  <div class="navbar-inner">
   <a class="brand" href="#">Meny</a>
    <ul class="nav">
      <li ><a href="index.py">Start</a></li>
      <li class="active"><a href="logs.py">Logs</a></li>
      <li><a href="exclude.py">Exclude</a></li>
      <li><a href="alert.py">Alert</a></li>
    </ul>
  </div>
</div>
<h1>Logs from SYCO Network</h1>
<h2>DATE : {0}</h2>
<h2>SIGNED : {1} </h2>

<table class="table table-striped">
""".format(view_date,signed)



result = search_logs(view_date)
for i in range(result.rowcount):
			row = result.fetchone()
			if row[2] == "kernel:":
				row_class="error"
			elif row[1] == "warning":
				row_class="warning"
			elif row[1] == "secuess":
				row_class="success"
			elif row[1] == "info":
				row_class="info"
			else:
				row_class="non"
				

			print "<tr class='{4}'><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td><a class='btn btn-danger' href='?exclude={3}''>Exclude</a></td></tr>".format(row[0],row[1],row[2],row[3],row_class)	


print """ 
<tr><td> </td><td>- </td></tr>
</table>

"""
if signed == "Not Signed" and not view_date == date.today():
	print """
		<form>
		<input type="hidden" name="view_date" value="{0}" />
		<input type="hidden" name="user" value="{1}" />
		<input type="text" name="mess" value="message"/><br>
		<button type="submit" class="btn-large btn-success">SIGN</button>
		</from>
		""".format(view_date,os.environ["SERVER_NAME"])
	print "<b>USER = "+os.environ["REMOTE_USER"]+"</b>"

print """
</div>
</body> 
 </html>
 """