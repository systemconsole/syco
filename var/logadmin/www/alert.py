#!/usr/bin/env python
 
import cgi
import os
from datetime import date, timedelta
from log_mysql import search_logs, logs_are_signed, sign_logs, add_exclude, get_exclude, del_exclude, add_alert, get_alert, del_alert, get_loghosts

import cgitb; cgitb.enable()  # for troubleshooting
# Create instance of FieldStorage 
form = cgi.FieldStorage() 


print "Content-type: text/html"

print """
<html> 
<head>
	<LINK href="css/bootstrap.css" rel="stylesheet" type="text/css">
	<title>Syco LogAdmin</title></head> 
<body> 
 """

#Excluding records
if form.getvalue('alert'):
	alert = form.getvalue('alert')
	status = form.getvalue('status')
	host = form.getvalue('host')
	add_alert(alert,status,host)

	print """
	<div class="alert alert-warning">
  	<h4>You have adden an alert for  <b>{0}</b> and wirh alert level <b>{1}</b>   
  	</div>
	""".format(alert,status)

#Deleting excludiing records
if form.getvalue('delete'):
	delete = form.getvalue('delete')
	del_alert(delete)

	print """
	<div class="alert alert-error">
  	<h4>You have deleted an alert from the database 
  	</div>
	""".format(delete)



print """
<div div class="container">
<div class="navbar">
  <div class="navbar-inner">
   <a class="brand" href="#">Meny</a>
    <ul class="nav">
      <li ><a href="index.py">Start</a></li>
      <li ><a href="logs.py">Logs</a></li>
      <li><a href="exclude.py">Exclude</a></li>
      <li><a class="active" href="alert.py">Alert</a></li>
    </ul>
  </div>
</div>
<h1>Logs from SYCO Network</h1>
<h2>Trigger alerts Strings</h2>
<form>
<p> - Write text to have alerts triggerd on
<ul><input class="input-large" type="text" name="alert" placeholder="Trigger input"/></ul>
<p>- CRITICAL will generate Nagios Critical Alert</p> 
<p>- WARNING will generate Nagioas Warning Alert</p>
<p>- OK will generate CRITICAL if NOT FOUND ON Host</p>
<ul><select name="status" class="">
<option>CRITICAL</option>
<option>WARNING</option>
<option>OK</option>
</select></ul>
<p>- Log from Hosts</p>
<ul><select name="host" class="">
<option>NONE</option>
"""
result = get_loghosts()
for i in range(result.rowcount):
	row = result.fetchone()
	print "<option>"+row[0]+"</option>"


print """
</select></ul>
<ul><input type="Submit" class="btn" name="button" value="Add Trigger"/></ul>
</form>
<table class="table">
<tr><td><h5>Triggers</h5></td><td><h5>By User</h5></td><td><h5>Added Date</h5></td><td><h5>Status</h5></td><td><h5>Host</h5></td></tr>
"""
result = get_alert()
for i in range(result.rowcount):
	row = result.fetchone()
	if row[4]=='CRITICAL':
		row_class="error"
	
	elif row[4]=='OK':
		row_class="success"

	else:
		row_class=""
	print "<tr class='{5}'><td>{0}</td><td>{1}</td><td><h5>{2}</h5></td><td>{4}</td><td>{6}</td><td><a href='?delete={3}'' class='btn btn-danger'>Delete</a></td></tr>".format(row[0],row[1],row[2],row[3],row[4],row_class,row[5])


print """
</div>
</body> 
 </html>
 """