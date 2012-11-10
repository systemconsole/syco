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
echo ""
echo $CMD
/usr/bin/env mysql -u"purgelogdb" -p"${MYSQL_PASSWORD}" Syslog -e"$CMD"
OUT=$?
if [ $OUT -ne 0 ]; then
	echo "[SYCO ERROR] purge rsyslgd mysql database failed."
	echo
    logger -p user.crit "[SYCO ERROR] purge rsyslgd mysql database failed."
else
	echo "[SYCO NOTICE] purged 100 days old rows from rsyslogd mysql database."
    logger "[SYCO NOTICE] purged 100 days old rows from rsyslogd mysql database."
fi
exit $OUT

