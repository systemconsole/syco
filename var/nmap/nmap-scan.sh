#!/bin/bash

# __author__ = "daniel@cybercow.se, anders@televerket.net"
# __copyright__ = "Copyright 2012, The System Console project"
# __maintainer__ = "Daniel Lindh"
# __email__ = "syco@cybercow.se"
# __credits__ = ["???"]
# __license__ = "???"
# __version__ = "1.0.0"
# __status__ = "Production"

NETWORK_NAME="${NMAP_NAME}"
TARGETS="${NMAP_TARGETS}"
OPTIONS="-v -T4 -F -sV"
DATE=`date +%F`

nmap $OPTIONS $TARGETS -oX /var/lib/nmap/scans/$NETWORK_NAME-$DATE-scan.xml
ndiff /var/lib/nmap/$NETWORK_NAME-initial-nmap.xml /var/lib/nmap/scans/$NETWORK_NAME-$DATE-scan.xml > /var/lib/nmap/scans/$NETWORK_NAME-$DATE-nmap-diff
OUT=$?
if [ $OUT -ne 0 ]; then
    txt="[ERROR] Network $NETWORK_NAME changes detected from NMAP Scan"
    echo $txt
    echo
    logger -t syco -p user.crit $txt
	cat /tmp/$NETWORK_NAME-$DATE-nmap-diff
	echo
else
    $txt="[NOTICE] NMAP scan completed, no changes detected."
    logger -t syco $txt
fi

# Create new initial-nmap
cp /var/lib/nmap/scans/$NETWORK_NAME-$DATE-scan.xml /var/lib/nmap/$NETWORK_NAME-initial-nmap.xml

exit $OUT
