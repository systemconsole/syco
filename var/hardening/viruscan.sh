#!/bin/bash

# email subject
SUBJECT="VIRUS DETECTED ON `hostname`!!!"
# Email To ?
EMAIL="sysoparenden@fareoffice.com"
#Date  for saving all scans
DATE=`date +%y-%m-%d`
# Log location
LOG=/var/log/clamav/scan-$DATE.log
echo $DATE

check_scan () {

        # Check the last set of results. If there are any "Infected" counts that aren't zero, we have a problem.
        if [ `tail -n 12 ${LOG}  | grep Infected | grep -v 0 | wc -l` != 0 ]
        then
                EMAILMESSAGE=`mktemp /tmp/virus-alert.XXXXX`
                echo "To: ${EMAIL}" >>  ${EMAILMESSAGE}
                echo "From: noreplay@fareoffice.com" >>  ${EMAILMESSAGE}
                echo "Subject: ${SUBJECT}" >>  ${EMAILMESSAGE}
                echo "Importance: High" >> ${EMAILMESSAGE}
                echo "X-Priority: 1" >> ${EMAILMESSAGE}
                echo "`tail -n 50 ${LOG}`" >> ${EMAILMESSAGE}
                /usr/sbin/sendmail -t < ${EMAILMESSAGE}
        fi

}
/usr/local/bin/freshclam
/usr/local/bin/clamscan -ir --exclude=/proc --exclude=/sys --exclude=/dev --exclude=/media --exclude=/mnt / --quiet --infected --log=${LOG}

check_scan
cat ${LOG} | logger