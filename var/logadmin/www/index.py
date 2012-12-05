#!/usr/bin/env python
 
import cgi
import os
from log_mysql import get_signed, search_logs
from datetime import date, timedelta
import cgitb; cgitb.enable()  # for troubleshooting
print "Content-type: text/html"
 
print """
<html> 
<head>
	<LINK href="css/bootstrap.css" rel="stylesheet" type="text/css">
	<title>Syco LogAdmin</title></head> 
<body> 
 """

 
print """
<div div class="container">
	<div class="navbar">
  <div class="navbar-inner">
    <a class="brand" href="#">Meny</a>
    <ul class="nav">
      <li class="active"><a href="index.py">Start</a></li>
      <li><a href="logs.py">Logs</a></li>
      <li><a href="exclude.py">Exclude</a></li>
      <li><a href="alert.py">Alert</a></li>
    </ul>
  </div>
</div>
<h1>Logs from SYCO Network</h1>
<h3>Login as {0}</h3>
<table class="table table-striped">
<tr><td><h4>DATE</h4></td><td><h4>SIGNED</h4></td><td><h4>SIGNED DATE</h4></td></tr
<tr><td><h5><a href="logs.py?id=now">Today</a></h5></td><td><h5></h5></td></tr>
""".format(os.environ["REMOTE_USER"])

signed_list = get_signed()
datum_dicu={}
datum_dicu_date={}
row = signed_list.fetchall()
for value in row:
	datum_dicu.update({value[0]:value[1]})
	datum_dicu_date.update({value[0]:value[2]})


num=0
for num in range(1,20):
	whatdate = str(date.today() - timedelta(num))
	if whatdate in datum_dicu:
		user = datum_dicu[whatdate]
	else:
		user = "Unsigned"

	if whatdate in datum_dicu_date:
		signdate = datum_dicu_date[whatdate]
	else:
		signdate = ""

	print """<tr><td><h5><a href="logs.py?view_date={0}">{0}</a></h5></td><td><h5>{1}</h5></td><td><h5>{2}</h5></td></tr>""".format(date.today() - timedelta(num),user,signdate)
	num=num+1


print """ 
<tr><td> </td><td>- </td></tr>
</table>
"""


print """

</div>
</body> 
 </html>
 """
