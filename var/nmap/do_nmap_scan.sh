#!/bin/sh
TARGETS="${nmap_targets}"
OPTIONS="-v -T4 -F -sV"
date=`date +%F`
#cd /var/lib/nmap/scans
nmap $OPTIONS $TARGETS -oX /var/lib/nmap/scans/scan-$date.xml > /dev/null
ndiff /var/lib/nmap/initial_nmap.xml /var/lib/nmap/scans/scan-$date.xml > /tmp/nmap_diff-$date
OUT=$?
if [ $OUT -ne 0 ]; then
	echo "Network changes detected from NMAP Scan"
	cat /tmp/nmap_diff-$date
	echo
fi
rm /tmp/nmap_diff-$date
exit $OUT
