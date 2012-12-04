#!/bin/bash

# __author__ = "anders@televerket.net, daniel@cybercow.se"
# __copyright__ = "Copyright 2012, The System Console project"
# __maintainer__ = "Daniel Lindh"
# __email__ = "syco@cybercow.se"
# __credits__ = ["???"]
# __license__ = "???"
# __version__ = "1.0.0"
# __status__ = "Production"

TARGETS="${NMAP_TARGETS}"
OPTIONS="-v -T4 -F -sV"
date=`date +%F`

nmap $OPTIONS $TARGETS -oX /var/lib/nmap/scans/$date-scan.xml
ndiff /var/lib/nmap/initial_nmap.xml /var/lib/nmap/scans/$date-scan.xml > /var/lib/nmap/scans/$date-nmap_diff
OUT=$?
if [ $OUT -ne 0 ]; then
    txt="[ERROR] Network changes detected from NMAP Scan"
    echo $txt
    echo
    logger -t syco -p user.crit $txt
	cat /tmp/$date-nmap_diff
	echo
else
    $txt="[NOTICE] NMAP scan completed, no changes detected."
    echo $txt
    echo
    logger -t syco $txt
fi

# Create new initial-nmap
cp /var/lib/nmap/scans/$date-scan.xml /var/lib/nmap/initial_nmap.xml

exit $OUT
