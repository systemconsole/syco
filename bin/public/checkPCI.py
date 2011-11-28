#! /usr/bin/env python
#
# PCI evendice extraxt for fareoffice
# Mattias Hemmingsson 2011
# mattias@fareoffice.com
import shlex, subprocess
from datetime import date


def main(cmd,filter,filename,append):
	now=date.today().strftime("%Y-%m-%d")
	hostname=subprocess.check_output(["hostname"],shell=True)
	host=hostname.rstrip("\n")
	if(append=="append"):
		o=open("/opt/stadard/"+host+"-"+filename+"-"+now+".txt",'a')
		print "appending"
	else:
		o=open("/opt/stadard/"+host+"-"+filename+"-"+now+".txt",'w')
	f=subprocess.Popen([cmd], stdout=subprocess.PIPE,shell=True).communicate()[0]
	for line in f.split("\n"):
		if filter in line:
			o.write(line+"\n")
	o.close()
	

if __name__ == "__main__":
	#use
	#main("comamnd to run","Search for","save as filenamn","append previus file")    
	main("cat /opt/passwd","/bin/bash","passwd","no")
	#main("cat /opt/shadow","","passwd","append")
 	#Netstat
 	#main("netstat -anp","LISTEN","2.2.1_2.2.2_2.2.3-netstat","no")
 	
 	#Antivirus
 	#main("netstat -anp","LISTEN","5.1_5.2-Antivirus","no")


 	#Patch Level
 	#main("netstat -anp","LISTEN","5.1-Patchlevel","no")

 	#Acces Level
	#main("netstat -anp","LISTEN","10.2.1_10.2.2_10.2.3_10.2.4_10.2.5_10.3.1_10.3.2_10.3.3_10.3.4_10.3.5_10.3.6-Accesslist","no")
	 	
 	#Password File
 	#main("netstat -anp","LISTEN","7.1_7.2.2_8.1_8.2_8.5.8_8.5.9_8.5.10_8.5.11_8.5.12_8.5.13_8.5.14_8.5.15-PasswordFile","no")
	
	#Password Settings
	#main("netstat -anp","LISTEN","7.1_7.2.2_8.1_8.2_8.5.8_8.5.9_8.5.10_8.5.11_8.5.12_8.5.13_8.5.14_8.5.15-PasswordSettings","no")

	#Session Timeout
	#main("netstat -anp","LISTEN","7.1_7.2.2_8.1_8.2_8.5.8_8.5.9_8.5.10_8.5.11_8.5.12_8.5.13_8.5.14_8.5.15-SessionTimeout","no")	

	#Log Sample
	#main("netstat -anp","LISTEN","10.2.1_10.2.2_10.2.3_10.2.4_10.2.5_10.3.1_10.3.2_10.3.3_10.3.4_10.3.5_10.3.6-LogSample","no")	

	#TimeSync
	#main("netstat -anp","LISTEN","5.1_5.2-TimeSync","no")
	
	#FIM Settings
	#main("netstat -anp","LISTEN","10.5.5-11.5-FimSettings","no")	