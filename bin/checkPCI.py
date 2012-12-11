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


# #!/bin/bash
# #################################################
# # Script for making server status rebort        #
# # Report includning PCI statmets		#
# #						#
# # mattias@fareoffice.com	version 0.1	#
# #################################################


# DIR=/var/log/

# #######Server values
# # Year Month Day
# YMD=`date +%Y-%m-%d`

# # Year Month Day Hour Minute
# YMDHM=`date +%Y-%m-%d_%H:%M`

# # DayOfWeek
# DOW=`date +%u%a`

# # DayOfMonth
# DOM=`date +%d`

# # Day And Month
# DAM=`date +%d%b`

# MON=`date +%b`



# ####################
# #Main menu

# status() {
# mkdir -p $DIR/`hostname`/$YMDHM/
# DEST=$DIR/`hostname`/$YMDHM/;



# echo "making `hostname` repport to $DEST";
# echo "Server Status------------------$YMDHM------------------------------" >> $DEST/`hostname`-ServerStatus
# echo "Server name : `hostname`" >> $DEST/`hostname`-ServerStatus
# echo "Kernel : `uname -a`" >> $DEST/`hostname`-ServerStatus
# echo "Processor :" >> $DEST/`hostname`-ServerStatus
# cat /proc/cpuinfo | grep model\ name >> $DEST/`hostname`-ServerStatus
# cat /proc/meminfo | grep MemTotal >> $DEST/`hostname`-ServerStatus
# cat /proc/meminfo | grep MemFree >> $DEST/`hostname`-ServerStatus


# ############OPEN PORTS
# echo "Open ports ---------------------$YMDHM------------------------------" >> $DEST/`hostname`-OpenPorts
# netstat -anp >> $DEST/`hostname`-OpenPorts

# ###################Firewall
# echo "`hostname` Firewall-------------$YMDHM-------------------------------" >> $DEST/`hostname`-Firewall
# /sbin/iptables -L >> $DEST/`hostname`-Firewall

# ########################Network
# echo "`hostname` Network---------------$YMDHM------------------------------" >> $DEST/`hostname`-Network
# /sbin/ifconfig >> $DEST/`hostname`-Network
# route >> $DEST/`hostname`-Network
# cat /etc/resolv.conf >> $DEST/`hostname`-Network


# #####################################Software Controll
# echo "`hostname` System Version Controll ----------$YMDHM------------------------------" >> $DEST/`hostname`-SoftWareControll
# echo "Redhat Release" >> $DEST/`hostname`-SoftWareControll
# cat /etc/redhat-release >> $DEST/`hostname`-SoftWareControll

# echo "Security Version" >> $DEST/`hostname`-SoftWareControll
# rpm -q security-blanket >> $DEST/`hostname`-SoftWareControll

# echo "Mysql Version" >> $DEST/`hostname`-SoftWareControll
# rpm -q mysql-server >> $DEST/`hostname`-SoftWareControll

# echo "Apache Version" >> $DEST/`hostname`-SoftWareControll
# rpm -q httpd >> $DEST/`hostname`-SoftWareControll

# echo "PHP Version" >> $DEST/`hostname`-SoftWareControll
# rpm -q php >> $DEST/`hostname`-SoftWareControll

# echo "Syslog Version" >> $DEST/`hostname`-SoftWareControll
# /usr/local/syslog-ng/sbin/syslog-ng -V >> $DEST/`hostname`-SoftWareControll

# echo "Yum System" >> $DEST/`hostname`-SoftWareControll
# yum check-update >> $DEST/`hostname`-SoftWareControll
# echo "Java Version---------------------------------------------------------------------" >> $DEST/`hostname`-SoftWareControll
# echo "`java -version`" >> $DEST/`hostname`-SoftWareControll

# echo "Glassfish Version---------------------------------------------------------------------" >> $DEST/`hostname`-SoftWareControll
# /opt/glassfish/bin/asadmin version >> $DEST/`hostname`-SoftWareControll



# ##################################################################System Values

# echo "`hostname` System Values ----------$YMDHM------------------------------" >> $DEST/`hostname`-SystemValues
# echo "Users -----------------------------------------------------------------" >> $DEST/`hostname`-SystemValues
# awk -F: '{print $1,$3}' /etc/passwd | while read user pid
# do
# echo $user >> $DEST/`hostname`-SystemValues
# done


# echo "Groups -----------------------------------------------------------------" >> $DEST/`hostname`-SystemValues
# awk -F: '{print $1,$3}' /etc/group | while read user pid
# do
# echo $user >> $DEST/`hostname`-SystemValues
# done

# echo "Password Settings -----------------------------------------------------------------" >> $DEST/`hostname`-SystemValues
# grep PASS /etc/login.defs >> $DEST/`hostname`-SystemValues

# echo "file Permission -----------------------------------------------------------" >> $DEST/`hostname`-SystemValues
# ls -l /etc/passwd >> $DEST/`hostname`-SystemValues
# ls -l /etc/group >> $DEST/`hostname`-SystemValues
# ls -l /etc/shadow >> $DEST/`hostname`-SystemValues

# echo "SSH Settings -----------------------------------------------------------" >> $DEST/`hostname`-SystemValues
# grep Protocol /etc/ssh/sshd_config >> $DEST/`hostname`-SystemValues


# echo "NTP Settings -----------------------------------------------------------" >> $DEST/`hostname`-SystemValues
# grep ntp /etc/crontab >> $DEST/`hostname`-SystemValues


# echo "Anivirus Settings -----------------------------------------------------------" >> $DEST/`hostname`-SystemValues
# grep freshclam /etc/crontab >> $DEST/`hostname`-SystemValues
# grep freshclam /etc/crontab >> $DEST/`hostname`-SystemValues


# ##############################################################################################LOGS

# echo "`hostname` System Logs ----------$YMDHM------------------------------" >> $DEST/`hostname`-Logs

# echo  "Inloggade användare denna månad -------------------------------------" >> $DEST/`hostname`-Logs
# awk -F: '/Accepted password/  {print $1,$3,$4}' /var/log/secure | while read mount val text
# do
# if [ $mount = $MON ]; then
#         echo $val $text >> $DEST/`hostname`-Logs
# fi
# done


# echo  "Sudo coammands------------------------------------" >> $DEST/`hostname`-Logs
# awk -F: '/sudo/  {print $1,$3,$4}' /var/log/secure | while read mount val text
# do
# if [ $mount = "$MON" ]; then
#         echo $val $text >> $DEST/`hostname`-Logs
# fi
# done



# echo  "Antivirus Uppdaterad månad -------------------------------------" >> $DEST/`hostname`-Logs
# awk -F: '/Database updated/  {print $1,$3,$4}' /var/log/messages | while read mount val text
# do
# if [ $mount = "$MON" ]; then
#         echo $val $text >> $DEST/`hostname`-Logs
# fi
# done

# echo  "NTP Updaterad -------------------------------------" >> $DEST/`hostname`-Logs
# awk -F: '/ntpdate/  {print $1,$3,$4}' /var/log/messages | while read mount val text
# do
# if [ $mount = "$MON" ]; then
#         echo $val $text >> $DEST/`hostname`-Logs
# fi
# done









# }

# mainMenu() {

# clear
# echo "Server Status"
# cat << EOF

# 	1) Save Server/Version Controll Status
#   2) Mail	Server/Version Controll Status

# Q) Quit

# EOF

# echo -n "chosse number from menu >  "

# read _my_choice

# case "$_my_choice" in
#  1) status ;;
#  2) save ;;
#  3) mail ;;
#  4) version ;;
#  5) mailVersion ;;
#  Q|q) exit ;;
# esac
# }

# if [ "$1" = '' ] ; then
# mainMenu

# elif [ "$1" = '-status' ] ; then
# 	status
# fi



