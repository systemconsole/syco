#!/bin/bash

# __author__ = "daniel@cybercow.se, anders@televerket.net"
# __copyright__ = "Copyright 2012, The System Console project"
# __maintainer__ = "Daniel Lindh"
# __email__ = "syco@cybercow.se"
# __credits__ = ["???"]
# __license__ = "???"
# __version__ = "1.0.0"
# __status__ = "Production"

CMD="DELETE FROM Syslog.SystemEvents WHERE ReceivedAt < DATE_SUB(NOW(), INTERVAL 100 DAY);"
/usr/bin/env mysql -u"purgelogdb" -p"${MYSQL_PASSWORD}" Syslog -e"$CMD"
OUT=$?
if [ $OUT -ne 0 ]; then
    txt="[ERROR] purge rsyslgd mysql database failed."
    echo $CMD
	echo $txt
	echo
    logger -t syco -p user.crit $txt
else
    txt="[NOTICE] purged 100 days old rows from rsyslogd mysql database."
    logger -t syco $txt
fi
exit $OUT

