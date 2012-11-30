#!/usr/bin/env python
 
import cgi
import os
from datetime import date, timedelta
from log_mysql import search_logs, logs_are_signed, sign_logs, add_exclude, get_exclude, del_exclude

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
if form.getvalue('exclude'):
	exclude = form.getvalue('exclude')
	status = form.getvalue('status')
	add_exclude(exclude,status)

	print """
	<div class="alert alert-warning">
  	<h4>You have exclude <b>{0}</b> from the log search
  	</div>
	""".format(exclude)

#Deleting excludiing records
if form.getvalue('delete'):
	delete = form.getvalue('delete')
	del_exclude(delete)

	print """
	<div class="alert alert-error">
  	<h4>You have deleted an exclud from the database 
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
      <li><a class="active" href="exclude.py">Exclude</a></li>
      <li><a href="alert.py">Alert</a></li>
    </ul>
  </div>
</div>
<h1>Logs from SYCO Network</h1>
<h2>Exclude from search</h2>
<form>
<p> - Write text to Delete / Exclude from logs
<ul><input class="input-large" type="text" name="exclude" placeholder="Text input"/></ul>
<p>- Delete will delete the result from the database</p> 
<p>- Exclude will exclude te entory from the search</p>
<ul><select name="status" class="">
<option>EXCLUDE</option>
<option>DELETE</option>
</select></ul>
<ul><input type="Submit" class="btn" name="button" value="Exclude"/></ul>
</form>
<table class="table">
<tr><td><h5>Exclude</h5></td><td><h5>By User</h5></td><td><h5>Added Date</h5></td><td><h5>Status</h5></td></tr>
"""
result = get_exclude()
for i in range(result.rowcount):
	row = result.fetchone()
	if row[4] =="DELETE":
		tr_class="error"
	else:
		tr_class=""
	print "<tr class='{5}'><td>{0}</td><td>{1}</td><td><h5>{2}</h5></td><td>{4}</td><td><a href='?delete={3}'' class='btn btn-danger'>Delete</a></td></tr>".format(row[0],row[1],row[2],row[3],row[4],tr_class)


print """
</div>
</body> 
 </html>
 """